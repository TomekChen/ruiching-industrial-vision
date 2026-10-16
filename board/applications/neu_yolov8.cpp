/**
 * 切片 D · NEU YOLOv8n NCNN 板端推理（可学习注释版）
 *
 * 和 yolov3.cpp 的差别（务必读懂）：
 * 1) 模型文件：neu_yolov8n.param / .bin（不是 mobilenetv2_yolov3.*）
 * 2) 输入/输出 blob：in0 / out0（不是 data / detection_out）
 * 3) 输入边长 320；预处理 = letterbox + RGB + /255（不是 352 + 127.5 均值）
 * 4) 输出张量形状 (10, 2100) = 4(xywh) + 6(NEU类分数)；图里已含 DFL 解码
 * 5) 板端仍要做：阈值过滤 → NMS → 坐标映射回原图
 *
 * msh 用法：
 *   cd /data
 *   neu_yolov8_test scratches_10.jpg out_neu_scratches_10.jpg
 *
 * 源码学习副本：仓库 board/applications/neu_yolov8.cpp
 * 编译工程副本：F:/ruiching-workspace/yolo_183/applications/neu_yolov8.cpp
 *
 * 注意：yolo_183 工程用完整 OpenCV（与 yolov3.cpp 一致），不是 simpleocv。
 */

#include <rtthread.h>
#include <rtdevice.h>

#include "layer.h"
#include "net.h"

#include <opencv2/core/core.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>

#include <algorithm>
#include <float.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <vector>

namespace
{

struct Object
{
    cv::Rect_<float> rect;
    int label;
    float prob;
};

static const char *kClassNames[] = {
    "open",
    "short",
    "mousebite",
    "spur",
    "copper",
    "pin-hole",
};
static const int kNumClass = 6;
static const int kTargetSize = 320;
static const float kConfThres = 0.25f;
static const float kNmsThres = 0.45f;

static inline float intersection_area(const Object &a, const Object &b)
{
    cv::Rect_<float> inter = a.rect & b.rect;
    return inter.area();
}

static void qsort_descent_inplace(std::vector<Object> &objects, int left, int right)
{
    int i = left;
    int j = right;
    float p = objects[(left + right) / 2].prob;
    while (i <= j)
    {
        while (objects[i].prob > p)
            i++;
        while (objects[j].prob < p)
            j--;
        if (i <= j)
        {
            std::swap(objects[i], objects[j]);
            i++;
            j--;
        }
    }
    if (left < j)
        qsort_descent_inplace(objects, left, j);
    if (i < right)
        qsort_descent_inplace(objects, i, right);
}

static void qsort_descent_inplace(std::vector<Object> &objects)
{
    if (objects.empty())
        return;
    qsort_descent_inplace(objects, 0, (int)objects.size() - 1);
}

static void nms_sorted_bboxes(const std::vector<Object> &objects, std::vector<int> &picked, float nms_threshold)
{
    picked.clear();
    const int n = (int)objects.size();
    std::vector<float> areas(n);
    for (int i = 0; i < n; i++)
        areas[i] = objects[i].rect.area();

    for (int i = 0; i < n; i++)
    {
        const Object &a = objects[i];
        int keep = 1;
        for (int j = 0; j < (int)picked.size(); j++)
        {
            const Object &b = objects[picked[j]];
            float inter = intersection_area(a, b);
            float union_area = areas[i] + areas[picked[j]] - inter;
            if (union_area > 0 && inter / union_area > nms_threshold)
            {
                keep = 0;
                break;
            }
        }
        if (keep)
            picked.push_back(i);
    }
}

/** letterbox：等比缩放 + 灰边填充到 target×target */
static cv::Mat letterbox(const cv::Mat &bgr, int target, float &scale, float &pad_w, float &pad_h)
{
    int img_w = bgr.cols;
    int img_h = bgr.rows;
    scale = std::min((float)target / img_w, (float)target / img_h);
    int new_w = (int)roundf(img_w * scale);
    int new_h = (int)roundf(img_h * scale);
    pad_w = (target - new_w) / 2.f;
    pad_h = (target - new_h) / 2.f;

    cv::Mat resized;
    cv::resize(bgr, resized, cv::Size(new_w, new_h));

    int top = (int)roundf(pad_h - 0.1f);
    int bottom = (int)roundf(pad_h + 0.1f);
    int left = (int)roundf(pad_w - 0.1f);
    int right = (int)roundf(pad_w + 0.1f);

    cv::Mat out;
    cv::copyMakeBorder(resized, out, top, bottom, left, right, cv::BORDER_CONSTANT, cv::Scalar(114, 114, 114));
    return out;
}

static int detect_neu_yolov8(const cv::Mat &bgr, std::vector<Object> &objects)
{
    ncnn::Net net;
    // 板子内存紧，默认关 Vulkan（需要时可改 true，与 yolov3 示例一致）
    net.opt.use_vulkan_compute = false;
    net.opt.num_threads = 2;

    if (net.load_param("neu_yolov8n.param"))
    {
        rt_kprintf("load_param neu_yolov8n.param failed\n");
        return -1;
    }
    if (net.load_model("neu_yolov8n.bin"))
    {
        rt_kprintf("load_model neu_yolov8n.bin failed\n");
        return -1;
    }

    int img_w = bgr.cols;
    int img_h = bgr.rows;

    float scale = 1.f;
    float pad_w = 0.f;
    float pad_h = 0.f;
    cv::Mat lb = letterbox(bgr, kTargetSize, scale, pad_w, pad_h);

    // Ultralytics：RGB + /255
    ncnn::Mat in = ncnn::Mat::from_pixels(lb.data, ncnn::Mat::PIXEL_BGR2RGB, kTargetSize, kTargetSize);
    const float norm_vals[3] = {1 / 255.f, 1 / 255.f, 1 / 255.f};
    in.substract_mean_normalize(0, norm_vals);

    ncnn::Extractor ex = net.create_extractor();
    ex.input("in0", in);

    ncnn::Mat out;
    ex.extract("out0", out);
    // 期望：out.w = num_anchors(2100), out.h = 4+nc(10)
    rt_kprintf("out shape w=%d h=%d c=%d\n", out.w, out.h, out.c);

    if (out.h < 4 + kNumClass)
    {
        rt_kprintf("unexpected out.h=%d (need >= %d)\n", out.h, 4 + kNumClass);
        return -1;
    }

    std::vector<Object> proposals;
    proposals.reserve(64);

    for (int i = 0; i < out.w; i++)
    {
        // 第 i 个 anchor：通道 0..3 = cx,cy,w,h（letterbox 320 坐标）；4.. = 类分数
        float cx = out.row(0)[i];
        float cy = out.row(1)[i];
        float bw = out.row(2)[i];
        float bh = out.row(3)[i];

        int best_label = 0;
        float best_score = out.row(4)[i];
        for (int c = 1; c < kNumClass; c++)
        {
            float s = out.row(4 + c)[i];
            if (s > best_score)
            {
                best_score = s;
                best_label = c;
            }
        }
        if (best_score < kConfThres)
            continue;

        Object obj;
        obj.label = best_label;
        obj.prob = best_score;
        obj.rect.x = cx - bw * 0.5f;
        obj.rect.y = cy - bh * 0.5f;
        obj.rect.width = bw;
        obj.rect.height = bh;
        proposals.push_back(obj);
    }

    qsort_descent_inplace(proposals);
    std::vector<int> picked;
    nms_sorted_bboxes(proposals, picked, kNmsThres);

    objects.clear();
    objects.resize(picked.size());
    for (int i = 0; i < (int)picked.size(); i++)
    {
        objects[i] = proposals[picked[i]];

        // letterbox 坐标 → 原图
        float x0 = (objects[i].rect.x - pad_w) / scale;
        float y0 = (objects[i].rect.y - pad_h) / scale;
        float x1 = (objects[i].rect.x + objects[i].rect.width - pad_w) / scale;
        float y1 = (objects[i].rect.y + objects[i].rect.height - pad_h) / scale;

        x0 = std::max(std::min(x0, (float)(img_w - 1)), 0.f);
        y0 = std::max(std::min(y0, (float)(img_h - 1)), 0.f);
        x1 = std::max(std::min(x1, (float)(img_w - 1)), 0.f);
        y1 = std::max(std::min(y1, (float)(img_h - 1)), 0.f);

        objects[i].rect.x = x0;
        objects[i].rect.y = y0;
        objects[i].rect.width = x1 - x0;
        objects[i].rect.height = y1 - y0;
    }

    rt_kprintf("proposals=%d kept=%d\n", (int)proposals.size(), (int)objects.size());
    return 0;
}

static void draw_objects(const cv::Mat &bgr, const std::vector<Object> &objects, const std::string &output_path)
{
    cv::Mat image = bgr.clone();
    for (size_t i = 0; i < objects.size(); i++)
    {
        const Object &obj = objects[i];
        const char *name = (obj.label >= 0 && obj.label < kNumClass) ? kClassNames[obj.label] : "?";
        rt_kprintf("%d %s = %.3f at %.1f %.1f %.1fx%.1f\n",
                   obj.label, name, obj.prob, obj.rect.x, obj.rect.y, obj.rect.width, obj.rect.height);

        cv::rectangle(image, obj.rect, cv::Scalar(0, 255, 0));

        char text[128];
        sprintf(text, "%s %.1f%%", name, obj.prob * 100);
        int baseLine = 0;
        cv::Size label_size = cv::getTextSize(text, cv::FONT_HERSHEY_SIMPLEX, 0.5, 1, &baseLine);
        int x = (int)obj.rect.x;
        int y = (int)obj.rect.y - label_size.height - baseLine;
        if (y < 0)
            y = 0;
        if (x + label_size.width > image.cols)
            x = image.cols - label_size.width;

        cv::rectangle(image,
                      cv::Rect(cv::Point(x, y), cv::Size(label_size.width, label_size.height + baseLine)),
                      cv::Scalar(0, 255, 0), -1);
        cv::putText(image, text, cv::Point(x, y + label_size.height),
                    cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(0, 0, 0));
    }
    cv::imwrite(output_path, image);
}

} // namespace

int neu_yolov8_test(int argc, char *argv[])
{
    rt_kprintf("NEU YOLOv8n NCNN test\n");
    char default_input[] = "scratches_10.jpg";
    char default_output[] = "out_neu.jpg";
    char *input_img;
    char *output_img;

    if (argc < 3)
    {
        input_img = default_input;
        output_img = default_output;
        rt_kprintf("usage: neu_yolov8_test <in.jpg> <out.jpg>\n");
        rt_kprintf(" fallback input=%s output=%s\n", input_img, output_img);
    }
    else if (argc == 3)
    {
        input_img = argv[1];
        output_img = argv[2];
        rt_kprintf(" input=%s output=%s\n", input_img, output_img);
    }
    else
    {
        rt_kprintf("invalid args\n");
        return -1;
    }

    rt_uint32_t t0 = 0, t1 = 0;

    rt_kprintf("imread start\n");
    t0 = rt_tick_get();
    cv::Mat m = cv::imread(input_img, 1);
    t1 = rt_tick_get();
    rt_kprintf("imread end : %d ms\n", t1 - t0);
    if (m.empty())
    {
        rt_kprintf("cv::imread failed: %s\n", input_img);
        return -1;
    }

    std::vector<Object> objects;
    rt_kprintf("detect start\n");
    t0 = rt_tick_get();
    int ret = detect_neu_yolov8(m, objects);
    t1 = rt_tick_get();
    rt_kprintf("detect end : %d ms (ret=%d)\n", t1 - t0, ret);
    if (ret != 0)
        return ret;

    rt_kprintf("draw start\n");
    t0 = rt_tick_get();
    draw_objects(m, objects, output_img);
    t1 = rt_tick_get();
    rt_kprintf("draw end : %d ms\n", t1 - t0);
    rt_kprintf("execute done, detections=%d\n", (int)objects.size());
    return 0;
}
MSH_CMD_EXPORT(neu_yolov8_test, NEU YOLOv8n NCNN industrial defect detect);
