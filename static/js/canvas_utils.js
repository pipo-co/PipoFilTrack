"use strict";

const CANVAS_RESOLUTION = 1000; // La resolucion horizontal, la vertical se calcula para mantener el aspect ratio

function drawLine(ctx, x0, y0, x1, y1, color = POINT_COLOR, width = LINE_WIDTH) {
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.lineWidth   = width;
    ctx.strokeStyle = color;
    ctx.stroke();
}

function drawPoint(ctx, x, y, color = POINT_COLOR, size = POINT_SIZE) {
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
}

function buildCanvas(frame) {
    const ret = document.createElement('canvas');
    ret.classList.add('canvas');

    return drawIntoCanvas(ret, frame);
}

function drawIntoCanvas(canvas, frame) {
    setResolution(canvas, frame.width, frame.height);

    const ctx = canvas.getContext('2d');
    canvasDisableSmoothing(ctx);
    ctx.drawImage(frame, 0, 0, canvas.width, canvas.height);

    return canvas;
}

function setResolution(canvas, width, height) {
    canvas.width = CANVAS_RESOLUTION;
    canvas.height = canvas.width / width * height;
}

function canvasDisableSmoothing(ctx) {
    // turn off image aliasing
    // https://stackoverflow.com/a/19129822/12270520
    ctx.msImageSmoothingEnabled     = false;
    ctx.webkitImageSmoothingEnabled = false;
    ctx.imageSmoothingEnabled       = false;
}

function trackingPoint2canvas({ x, y }, canvas, img) {
    return [pixel2CanvasPos(x, canvas.width, img.width), pixel2CanvasPos(y, canvas.height, img.height)];
  }
  
  function canvasPos2Pixel(pos, canvas_len, img_len, offset = 0) {
    return Math.trunc(pos / canvas_len * img_len) + offset;
  }
  
  function pixel2CanvasPos(pixel, canvas_draw_len, img_len, offset = 0) {
    return (pixel - offset) / img_len * canvas_draw_len;
  }
  