// Constants
const CANVAS_RESOLUTION = 1000; // La resolucion horizontal, la vertical se calcula para mantener el aspect ratio
const POINT_SIZE        = 10;
const LINE_WIDTH        = 5;
const POINT_COLOR       = '#ff0000';

// Elementos de UI
const canvas        = document.getElementById('points-selector-canvas');
const form          = document.getElementById('tracking-form');
const imgSelector   = document.getElementById('img-selector');
const errors        = document.getElementById('errors');
const undo          = document.getElementById('undo');
const redo          = document.getElementById('redo');
const resultImgs    = document.getElementById('result-imgs');

/* ------ Global data -------- */
// Points info
const selected_points   = [];
const redo_points       = [];

// Image and canvas info
let imageData;
let img_w;
let img_h;

(function () {
    form.addEventListener('submit', executeTracking);

    imgSelector.addEventListener('change', handleImageSelection);

    canvas.addEventListener('click', onCanvasClick);
    canvas.style.display = 'none';
    canvas.width = CANVAS_RESOLUTION;

    // Undo/Redo selected points
    undo.addEventListener('click', undoPoint);
    redo.addEventListener('click', redoPoint);
})();

function executeTracking(e) {
    if(selected_points.length < 2) {
        errors.innerText = 'Debe seleccionar el punto inicial y final del filamento';
    } else {
        // TODO(tobi): Request del form mediante fetch api. Incluirle los selected points.
    }

    e.preventDefault();
}

function canvasPos2Pixel(pos, canvas_len, img_len) {
    return Math.trunc(pos / canvas_len * img_len)
}
function canvasPos2PixelX(x, canvas_w) {
    return canvasPos2Pixel(x, canvas_w, img_w);
}
function canvasPos2PixelY(y, canvas_h) {
    return canvasPos2Pixel(y, canvas_h, img_h);
}

function pixel2CanvasPos(pixel, canvas_draw_len, img_len) {
    // Agregamos 0.5 para que se muestre en el medio del pixel, no en la esquina
    return (pixel + 0.5) / img_len * canvas_draw_len;
}
function pixel2CanvasPosX(x) {
    return pixel2CanvasPos(x, canvas.width, img_w);
}
function pixel2CanvasPosY(y) {
    return pixel2CanvasPos(y, canvas.height, img_h);
}

function onCanvasClick(event) {
    let rect = canvas.getBoundingClientRect();
    let x = event.clientX - rect.left;
    let y = event.clientY - rect.top;

    let pixel_x = canvasPos2PixelX(x, rect.width);
    let pixel_y = canvasPos2PixelY(y, rect.height);

    // Si agregas un punto, perdes los redo
    redo_points.length = 0;

    addPoint({x: pixel_x, y: pixel_y});
}

function addPoint(point) {
    point.prev = selected_points.length > 0
        ? selected_points[selected_points.length - 1]
        : null
        ;
    selected_points.push(point);

    updateInterface();
    drawPoint(point);
}

function drawPoint(point) {
    let ctx = canvas.getContext("2d");

    let x = pixel2CanvasPosX(point.x);
    let y = pixel2CanvasPosY(point.y);

    // Line
    if(point.prev) {
        let previousPoint = point.prev;
        ctx.beginPath();
        ctx.moveTo(pixel2CanvasPosX(previousPoint.x), pixel2CanvasPosY(previousPoint.y));
        ctx.lineTo(x, y);
        ctx.lineWidth   = LINE_WIDTH;
        ctx.strokeStyle = POINT_COLOR;
        ctx.stroke();
    }

    // Point
    ctx.beginPath();
    ctx.arc(x, y, POINT_SIZE, 0, Math.PI * 2);
    ctx.fillStyle = POINT_COLOR;
    ctx.fill();
}

function undoPoint() {
    let ctx = canvas.getContext("2d");

    if(selected_points.length > 0) {
        redo_points.push(selected_points.pop());

        // Clean canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Redraw image
        // TODO(tobi): Pasarlo a una funcion auxiliar
        const tmpCanvas = document.createElement('canvas');
        tmpCanvas.height = img_h;
        tmpCanvas.width = img_w;

        const tmpCtx = tmpCanvas.getContext('2d');
        tmpCtx.putImageData(imageData, 0, 0, 0, 0, img_w, img_h);

        canvasDisableSmoothing(ctx);
        ctx.drawImage(tmpCanvas, 0, 0, canvas.width, canvas.height);

        // Redraw all poins
        selected_points.forEach(drawPoint)
        updateInterface();
    }
}

function redoPoint() {
    if(redo_points.length > 0) {
        const point = redo_points.pop();
        addPoint(point)
    }
}

function updateInterface() {
    undo.style.visibility = selected_points.length === 0 ? 'hidden' : 'visible';
    redo.style.visibility = redo_points.length === 0 ? 'hidden' : 'visible';
    errors.innerText = '';
}

function canvasDisableSmoothing(ctx) {
    // turn off image aliasing
    // https://stackoverflow.com/a/19129822/12270520
    ctx.msImageSmoothingEnabled     = false;
    ctx.webkitImageSmoothingEnabled = false;
    ctx.imageSmoothingEnabled       = false;
}

// Empty selected points and build canvas for point selection
async function handleImageSelection() {
    if(imgSelector.length === 0) {
          // No nos subieron nada
          errors.innerText = 'No image selected';
          return;
    }

  let first = imgSelector.files[0];

  if(first.type === 'image/tiff') {
        const buffer = await first.arrayBuffer();
        const ifds = UTIF.decode(buffer);
    const ifd = ifds[0];
    UTIF.decodeImage(buffer, ifd, ifds);

    const rgbaData = UTIF.toRGBA8(ifd);
    imageData = new ImageData(new Uint8ClampedArray(rgbaData), ifd.width, ifd.height);

    img_w = ifd.width;
    img_h = ifd.height;
    canvas.height = canvas.width / img_w * img_h;

    const tmpCanvas = document.createElement('canvas');
    tmpCanvas.height = img_h;
    tmpCanvas.width = img_w;

    // Rendereamos la imagen en un canvas intermedio para luego poder escalar la imagen
    const tmpCtx = tmpCanvas.getContext('2d');
    tmpCtx.putImageData(imageData, 0, 0, 0, 0, img_w, img_h);

    let ctx = canvas.getContext('2d');
    canvasDisableSmoothing(canvas.getContext('2d'));
    ctx.drawImage(tmpCanvas, 0, 0, canvas.width, canvas.height);
  } else {
    errors.innerText = 'Image type not supports yet';
    return;
  }

  // Show canvas
  canvas.style.display = '';

  // Reset selected points
  selected_points.length    = 0;
  redo_points.length        = 0;
}
