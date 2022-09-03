export function drawLine(ctx, x0, y0, x1, y1, color, width) {
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.lineWidth   = width;
    ctx.strokeStyle = color;
    ctx.stroke();
}

export function drawPoint(ctx, x, y, color, size) {
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
}

export function buildImageCanvas(image, canvasWidth) {
    const ret = document.createElement('canvas');
    ret.width = canvasWidth;
    return drawIntoCanvas(ret, image);
}

export function drawIntoCanvas(canvas, image) {
  resizeCanvasHeight(canvas, image.width, image.height);

  const ctx = canvas.getContext('2d');
  canvasDisableSmoothing(ctx);
  ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

  return canvas;
}

export function drawIntoCanvasZoomed(canvas, image, imgOffset, zoomFactor, pointSelectorWidth, pointSelectorHeight) {
    resizeCanvasHeight(canvas, image.width, image.height, 2);

    const ctx = canvas.getContext('2d');
    canvasDisableSmoothing(ctx);
    ctx.drawImage(image, (imgOffset.x / pointSelectorWidth) * image.width, (imgOffset.y / pointSelectorHeight) * image.height, Math.trunc(image.width / zoomFactor), Math.trunc(image.height / zoomFactor), 0, 0, canvas.width, canvas.height);

    return canvas;
}

// Adjust canvas vertical size to maintain width * height aspect ratio
// Also if image is too wide we have to adjust height vh to fit the hole image
export function resizeCanvasHeight(canvas, width, height, correction = 1) {
    let percentage = height / width;
    if (percentage < 0.85 ) {
      canvas.style.height = 100 * percentage ** correction + "vh" 
    }
    canvas.height = canvas.width / width * height;
}

export function canvasDisableSmoothing(ctx) {
    // turn off image aliasing
    // https://stackoverflow.com/a/19129822/12270520
    ctx.msImageSmoothingEnabled     = false;
    ctx.webkitImageSmoothingEnabled = false;
    ctx.imageSmoothingEnabled       = false;
}

export function trackingPoint2canvas({ x, y }, canvas, img) {
    return [pixel2CanvasPos(x, canvas.width, img.width), pixel2CanvasPos(y, canvas.height, img.height)];
}

export function canvasPos2Pixel(pos, canvas_len, img_len, offset = 0) {
    return Math.trunc(pos / canvas_len * img_len) + offset;
}
  
export function pixel2CanvasPos(pixel, canvas_draw_len, img_len, offset = 0) {
    return (pixel - offset) / img_len * canvas_draw_len;
}
