// Constants
const CANVAS_RESOLUTION = 1000; // La resolucion horizontal, la vertical se calcula para mantener el aspect ratio
const POINT_SIZE        = 10;
const LINE_WIDTH        = 5;
const POINT_COLOR       = '#ff0000';

const TRACKING_POINT_SIZE           = 5;
const TRACKING_POINT_STATUS_COLOR   = {
    'INTERPOLATED': '#ff0000',
    'DELETED':      '#d608e5',
    null:           '#0055ff',
    undefined:      '#0055ff',
}
const NORMAL_LINE_COLOR     = 'rgba(0,255,255,0.22)'

// Elementos de UI
const selectorCanvas    = document.getElementById('points-selector-canvas');
const form              = document.getElementById('tracking-form');
const imgInput          = document.getElementById('img-input');
const errors            = document.getElementById('errors');
const undo              = document.getElementById('undo');
const redo              = document.getElementById('redo');
const resultImgs        = document.getElementById('result-imgs');
const results           = document.getElementById('results');
const downloadJson      = document.getElementById('download-json');
const downloadTsv       = document.getElementById('download-tsv');

/* ------ Global data -------- */
// Points info
const selected_points   = [];
const redo_points       = [];

// Image and canvas info
let selectorDrawable;

(function () {
    // Results initially not visible
    results.style.display = 'none';

    form.addEventListener('submit', executeTracking);

    imgInput.addEventListener('change', handleImageSelection);

    selectorCanvas.style.display = 'none';
    selectorCanvas.width = CANVAS_RESOLUTION;
    selectorCanvas.addEventListener('click', onCanvasClick);

    // Undo/Redo selected points
    undo.addEventListener('click', undoPoint);
    redo.addEventListener('click', redoPoint);
})();

function executeTracking(e) {
    e.preventDefault();
    clearError();

    if(selected_points.length < 2) {
        errors.innerText = 'Debe seleccionar el punto inicial y final del filamento';
        return;
    }

    const formData = new FormData(form);
    formData.append('points', JSON.stringify(selected_points));

    fetch('http://localhost:5000/track', {
        method: 'POST',
        body: formData,
    })
    .catch(error => showError('Server Connection Error: ' + error))
    .then(async response => {
        const body = await response.json();
        if(response.ok) {
            await renderTrackingResult(body);
        } else {
            showError(body.message);
        }
    })
    ;
}

async function renderTrackingResult(trackingResult) {
    resultImgs.innerHTML = '';
    resultImgs.style.display = 'none';

    // We iterate frame results and images at the same time (should have same length)
    const framesResultIter = trackingResult.frames[Symbol.iterator]();
    for await (const frame of drawableIterator(imgInput.files)) {
        const result = framesResultIter.next().value;
        const canvas = buildCanvas(frame);
        const ctx = canvas.getContext('2d');

        for(const point of result.points) {
            const [x, y] = trackingPoint2canvas(point, canvas, frame);
            drawPoint(ctx, x, y, TRACKING_POINT_STATUS_COLOR[point.status], TRACKING_POINT_SIZE);
        }

        for(const segment of result.metadata.normal_lines) {
            const [x0, y0] = trackingPoint2canvas(segment.start, canvas, frame);
            const [x1, y1] = trackingPoint2canvas(segment.end, canvas, frame);
            drawLine(ctx, x0, y0, x1, y1, NORMAL_LINE_COLOR);
        }

        resultImgs.appendChild(canvas);
    }

    downloadJson.href   = URL.createObjectURL(new Blob([toJsonResults(trackingResult)], {type: 'application/json'}));
    downloadTsv.href    = URL.createObjectURL(new Blob([toTsvResults(trackingResult)],  {type: 'application/json'}));

    resultImgs.style.display = '';
    results.style.display = '';
}

function toJsonResults(results) {
    const redactedResults = results.frames.map(frame => { return {
        points: frame.points.map(point => { return {
            x: point.x,
            y: point.y,
        }}),
    }});
    return JSON.stringify(redactedResults);
}

function toTsvResults(results) {
    const ret = ['frame\tx\ty'];

    let frame = 0;
    for(const result of results.frames) {
        result.points.forEach(point => ret.push([frame, point.x, point.y].join('\t')));
        frame++;
    }

    return ret.join('\r\n');
}

function trackingPoint2canvas({x, y}, canvas, img) {
    return [pixel2CanvasPosX(x, canvas, img), pixel2CanvasPosY(y, canvas, img)];
}

function buildCanvas(frame) {
    const ret = document.createElement('canvas');
    ret.classList.add('canvas');

    ret.width = CANVAS_RESOLUTION;
    ret.height = ret.width / frame.width * frame.height;

    const ctx = ret.getContext('2d');
    canvasDisableSmoothing(ctx);
    ctx.drawImage(frame, 0, 0, ret.width, ret.height);

    return ret;
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
    return pixel / img_len * canvas_draw_len;
}
function pixel2CanvasPosX(x, canvas, img) {
    return pixel2CanvasPos(x, canvas.width, img.width);
}
function pixel2CanvasPosY(y, canvas, img) {
    return pixel2CanvasPos(y, canvas.height, img.height);
}

function onCanvasClick(event) {
    const rect = selectorCanvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const pixel_x = canvasPos2PixelX(x, rect.width);
    const pixel_y = canvasPos2PixelY(y, rect.height);

    // Si agregas un punto, perdes los redo
    redo_points.length = 0;

    addPointSelection({x: pixel_x, y: pixel_y});
}

function addPointSelection(point) {
    point.prev = selected_points.length > 0
        ? selected_points[selected_points.length - 1]
        : null
        ;
    selected_points.push(point);

    updateInterface();
    drawPointSelection(point);
}

function drawPointSelection(point) {
    const ctx = selectorCanvas.getContext("2d");

    // Agregamos 0.5 para que se muestre en el medio del pixel, no en la esquina
    const x = pixel2CanvasPosX(point.x + 0.5, selectorCanvas, selectorDrawable);
    const y = pixel2CanvasPosY(point.y + 0.5, selectorCanvas, selectorDrawable);

    // Line
    if(point.prev) {
        const prev = point.prev;
        const prevX = pixel2CanvasPosX(prev.x + 0.5, selectorCanvas, selectorDrawable);
        const prevY = pixel2CanvasPosY(prev.y + 0.5, selectorCanvas, selectorDrawable);
        drawLine(ctx, prevX, prevY, x, y, POINT_COLOR)
    }

    drawPoint(ctx, x, y);
}

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

function undoPoint() {
    const ctx = selectorCanvas.getContext("2d");

    if(selected_points.length > 0) {
        redo_points.push(selected_points.pop());

        // Clean canvas
        ctx.clearRect(0, 0, selectorCanvas.width, selectorCanvas.height);

        // Redraw image
        canvasDisableSmoothing(ctx);
        ctx.drawImage(selectorDrawable, 0, 0, selectorCanvas.width, selectorCanvas.height);

        // Redraw all poins
        selected_points.forEach(drawPointSelection)
        updateInterface();
    }
}

function redoPoint() {
    if(redo_points.length > 0) {
        const point = redo_points.pop();
        addPointSelection(point)
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
    if(imgInput.files.length === 0) {
          // No nos subieron nada
          showError('No images selected');
          imgInput.value = '';
          return;
    }

    const firstDrawable = await drawableIterator(imgInput.files).next();
    if(!firstDrawable || firstDrawable.done) {
        showError('No valid image selected');
        imgInput.value = '';
        return;
    }

    // Get selector drawable value
    selectorDrawable = firstDrawable.value;

    // Update selector canvas with new drawable
    selectorCanvas.height = selectorCanvas.width / selectorDrawable.width * selectorDrawable.height;
    const ctx = selectorCanvas.getContext('2d');
    canvasDisableSmoothing(ctx);
    ctx.drawImage(selectorDrawable, 0, 0, selectorCanvas.width, selectorCanvas.height);

    // Show canvas
    selectorCanvas.style.display = '';

    // Reset selected points
    selected_points.length    = 0;
    redo_points.length        = 0;
}
