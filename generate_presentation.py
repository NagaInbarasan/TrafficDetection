from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

def create_presentation():
    prs = Presentation()

    # 1. Title Slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Traffic Flow Prediction Using Pretrained AI"
    subtitle.text = "Real-time Computer Vision, Tracking, and Forecasting\nUsing YOLOv8, ByteTrack, and Holt's Trend"

    # 2. Computer Vision Pipeline
    bullet_slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(bullet_slide_layout)
    title = slide.shapes.title
    title.text = "Computer Vision Pipeline"
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.text = "Real-time frame processing from actual video footage"
    p = tf.add_paragraph()
    p.text = "OpenCV VideoCapture: Efficient frame-by-frame extraction"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "YOLO (yolo26s.pt): High-accuracy pretrained vehicle detection"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "ByteTrack: Persistent multi-object tracking IDs"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Real-time AI annotation directly on the live frames"
    p.level = 1

    # 3. Bidirectional Geometric Counting
    slide = prs.slides.add_slide(bullet_slide_layout)
    title = slide.shapes.title
    title.text = "Bidirectional Geometric Counting"
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.text = "Accurate vehicle counting and direction assignment"
    p = tf.add_paragraph()
    p.text = "Configurable Counting Line: Adjustable via UI slider"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Vector Math (Cross Product): Determines line crossings geometrically"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Direction Tracking: Distinguishes Forward vs Reverse flow"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Duplicate Prevention: Prevents multiple counts for slow vehicles"
    p.level = 1

    # 4. Empirical Time-Series Forecasting
    slide = prs.slides.add_slide(bullet_slide_layout)
    title = slide.shapes.title
    title.text = "Empirical Time-Series Forecasting"
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.text = "Forecasting based on actual observed video data"
    p = tf.add_paragraph()
    p.text = "Time Windows: Aggregating crossings every 10 seconds"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Algorithm: Holt's Damped Linear Trend"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Damping Factor (\u03c6 = 0.85): Smooths predictions over time"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Horizons: Predicts 1-min, 5-min, and 10-min future flow"
    p.level = 1

    # 5. System Architecture
    slide = prs.slides.add_slide(bullet_slide_layout)
    title = slide.shapes.title
    title.text = "System Architecture"
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.text = "Modern, modular, and performant backend"
    p = tf.add_paragraph()
    p.text = "Python & Flask: Asynchronous video processing and REST APIs"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "SQLite Database: Isolated video sessions and historical metrics"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Hardware Acceleration: PyTorch with CUDA for RTX GPUs"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Frontend Integration: Dynamic JS fetching and Chart.js rendering"
    p.level = 1

    # 6. Dashboard & UI Features
    slide = prs.slides.add_slide(bullet_slide_layout)
    title = slide.shapes.title
    title.text = "Dashboard & UI Features"
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.text = "Single consolidated real-time analytics interface"
    p = tf.add_paragraph()
    p.text = "Single AI Video Panel: Directly displays MJPEG stream"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Dynamic Line Controls: Preset profiles (Highway/City) & Reverse toggle"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Live Key Performance Indicators (KPIs): FPS, Model, Device"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Visualizations: Time-series volume flow and vehicle class distributions"
    p.level = 1

    # 7. Performance & Benchmarking
    slide = prs.slides.add_slide(bullet_slide_layout)
    title = slide.shapes.title
    title.text = "Performance & Benchmarking"
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.text = "Reliable real-time operation"
    p = tf.add_paragraph()
    p.text = "CUDA Acceleration: Achieving real-time inference speeds"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Flexible Model Usage: Switch between Nano, Small, and Medium weights"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Automated Benchmarking Script: Verifies FPS, latency, and counts"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "No Synthetic Generation: Strict reliance on true video processing"
    p.level = 1

    prs.save('Traffic_Flow_Project_Overview.pptx')
    print("Successfully generated Traffic_Flow_Project_Overview.pptx")

if __name__ == '__main__':
    create_presentation()
