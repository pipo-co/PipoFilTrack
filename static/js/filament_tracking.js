// Constants
const CANVAS_RESOLUTION = 1000; // La resolucion horizontal, la vertical se calcula para mantener el aspect ratio
const POINT_SIZE        = 10;
const LINE_WIDTH        = 5;
const POINT_COLOR       = '#ff0000';

// Elementos de UI
const selectorCanvas    = document.getElementById('points-selector-canvas');
const form              = document.getElementById('tracking-form');
const imgSelector       = document.getElementById('img-selector');
const errors            = document.getElementById('errors');
const undo              = document.getElementById('undo');
const redo              = document.getElementById('redo');
const resultImgs        = document.getElementById('result-imgs');

/* ------ Global data -------- */
// Points info
const selected_points   = [];
const redo_points       = [];

// Image and canvas info
let selectorDrawable;

(function () {
    form.addEventListener('submit', executeTracking);

    imgSelector.addEventListener('change', handleImageSelection);

    selectorCanvas.addEventListener('click', onCanvasClick);
    selectorCanvas.style.display = 'none';
    selectorCanvas.width = CANVAS_RESOLUTION;

    // Undo/Redo selected points
    undo.addEventListener('click', undoPoint);
    redo.addEventListener('click', redoPoint);
})();

function executeTracking(e) {
    e.preventDefault();

    if(selected_points.length < 2) {
        errors.innerText = 'Debe seleccionar el punto inicial y final del filamento';
        return;
    }

    // TODO(tobi): Request del form mediante fetch api. Incluirle los selected points.
}

// In case of error returns error message
async function* drawableIterator(images) {
    // Files is not iterable
    for(const image of images) {

        // TODO(tobi): Agregar soporte para avi, png, jpg, etc
        if(image.type === 'image/tiff') {
            const buffer = await image.arrayBuffer();
            const ifds = UTIF.decode(buffer);
            for(const ifd of ifds) {
                UTIF.decodeImage(buffer, ifd, ifds);

                const rgbaData = UTIF.toRGBA8(ifd);
                const imageData = new ImageData(new Uint8ClampedArray(rgbaData), ifd.width, ifd.height);

                const drawable = document.createElement('canvas');
                drawable.width = ifd.width;
                drawable.height = ifd.height;

                // Rendereamos la imagen en un canvas intermedio para luego poder escalar la imagen
                const ctx = drawable.getContext('2d');
                ctx.putImageData(imageData, 0, 0, 0, 0, ifd.width, ifd.height);

                yield drawable;
            }
        } else {
            // Ignoramos tipos que no conocemos
        }
    }
}

function showError(message) {
    errors.innerText = message;
}

function clearError() {
    errors.innerText = '';
}

function canvasPos2Pixel(pos, canvas_len, img_len) {
    return Math.trunc(pos / canvas_len * img_len)
}
function canvasPos2PixelX(x, canvas_w) {
    return canvasPos2Pixel(x, canvas_w, selectorDrawable.width);
}
function canvasPos2PixelY(y, canvas_h) {
    return canvasPos2Pixel(y, canvas_h, selectorDrawable.height);
}

function pixel2CanvasPos(pixel, canvas_draw_len, img_len) {
    // Agregamos 0.5 para que se muestre en el medio del pixel, no en la esquina
    return (pixel + 0.5) / img_len * canvas_draw_len;
}
function pixel2CanvasPosX(x) {
    return pixel2CanvasPos(x, selectorCanvas.width, selectorDrawable.width);
}
function pixel2CanvasPosY(y) {
    return pixel2CanvasPos(y, selectorCanvas.height, selectorDrawable.height);
}

function onCanvasClick(event) {
    let rect = selectorCanvas.getBoundingClientRect();
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
    let ctx = selectorCanvas.getContext("2d");

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
    let ctx = selectorCanvas.getContext("2d");

    if(selected_points.length > 0) {
        redo_points.push(selected_points.pop());

        // Clean canvas
        ctx.clearRect(0, 0, selectorCanvas.width, selectorCanvas.height);

        // Redraw image
        canvasDisableSmoothing(ctx);
        ctx.drawImage(selectorDrawable, 0, 0, selectorCanvas.width, selectorCanvas.height);

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
    clearError();
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
    if(imgSelector.files.length === 0) {
          // No nos subieron nada
          showError('No images selected');
          imgSelector.value = '';
          return;
    }

    const firstDrawable = await drawableIterator(imgSelector.files).next();
    if(!firstDrawable || firstDrawable.done) {
        showError('No valid image selected');
        imgSelector.value = '';
        return;
    }

    // Get selector drawable value
    selectorDrawable = firstDrawable.value;

    // Update selector canvas with new drawable
    selectorCanvas.height = selectorCanvas.width / selectorDrawable.width * selectorDrawable.height;
    let ctx = selectorCanvas.getContext('2d');
    canvasDisableSmoothing(selectorCanvas.getContext('2d'));
    ctx.drawImage(selectorDrawable, 0, 0, selectorCanvas.width, selectorCanvas.height);

    // Show canvas
    selectorCanvas.style.display = '';

    // Reset selected points
    selected_points.length    = 0;
    redo_points.length        = 0;
}
