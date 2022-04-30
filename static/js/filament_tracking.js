const POINT_SIZE = 4;
const POINT_COLOR = '#ff0000';
let selected_points = [];
let redo_points = [];

let form
let canvas
let toggle

const images = {}

let img_height;
let img_width;

let canvas_draw_width;
let canvas_draw_height;

window.addEventListener('load', () => {

    canvas = document.getElementById('canvas');
    form = document.getElementById('tracking_form')
    toggle = document.getElementById('toggle_filter');

    img_height = canvas.dataset.img_height;
    img_width = canvas.dataset.img_width;

    // width dependiente del viewport. Hacemos que height respete el aspect ratio de la imagen
    canvas.height = canvas.width / img_width * img_height;

    canvas_draw_width = canvas.width;
    canvas_draw_height = canvas.height;

    const image_datalist = document.getElementById('image_urls');
    for (let option of image_datalist.options) {
        images[option.value] = option.text;
    }

    canvas.style.backgroundImage = `url(${images['original']})`;

    canvas.addEventListener('click', clickHandle);

    document.getElementById('undo').addEventListener('click', undoPoint);

    document.getElementById('redo').addEventListener('click', redoPoint);

    form.addEventListener('submit', formSubmitHandler);

    toggle.addEventListener('change', () => {
        let imgURL = images['original']
        
        if(toggle.checked) {
            imgURL = images['filtered']
        }
        canvas.style.backgroundImage = `url(${imgURL})`;
    })

});

function formSubmitHandler(ev) {
    if (selected_points.length < 2) {
        const div = document.createElement('div');
        div.className = 'flashes mt-2';
        div.innerHTML = '<p>Debe seleccionar el punto inicial y final del filamento</p>';
        document.getElementById('section_tracking_form').appendChild(div);
        ev.preventDefault();
        return;
    }

    form['points'].value = JSON.stringify(selected_points);
    form.submit();
}

function canvasPos2Pixel(pos, canvas_len, img_len) {
    return Math.trunc(pos / canvas_len * img_len)
}
function canvasPos2PixelX(x, canvas_width) {
    return canvasPos2Pixel(x, canvas_width, img_width);
}
function canvasPos2PixelY(y, canvas_height) {
    return canvasPos2Pixel(y, canvas_height, img_height);
}

function pixel2CanvasPos(pixel, canvas_draw_len, img_len) {
    // Agregamos 0.5 para que se muestre en el medio del pixel, no en la esquina
    return (pixel + 0.5) / img_len * canvas_draw_len;
}
function pixel2CanvasPosX(x) {
    return pixel2CanvasPos(x, canvas_draw_width, img_width);
}
function pixel2CanvasPosY(y) {
    return pixel2CanvasPos(y, canvas_draw_height, img_height);
}

function clickHandle(event) {
    let rect = canvas.getBoundingClientRect();
    let x = event.clientX - rect.left;
    let y = event.clientY - rect.top;

    let pixel_x = canvasPos2PixelX(x, rect.width);
    let pixel_y = canvasPos2PixelY(y, rect.height);

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
        ctx.strokeStyle = POINT_COLOR;
        ctx.stroke();
    }
    
    // Point
    ctx.beginPath();
    ctx.arc(x, y, POINT_SIZE, 0, Math.PI * 2);
    ctx.fillStyle = POINT_COLOR;
    ctx.fill();
}

function undoPoint(){
    let ctx = canvas.getContext("2d");

    if (selected_points.length > 0) {
        redo_points.push(selected_points.pop());
        
        // Clean canvas
        ctx.clearRect(0, 0, canvas_draw_width, canvas_draw_height);
        
        // Redraw all poins
        selected_points.forEach(drawPoint)
        updateInterface();
    }
}

function redoPoint(){
    if (redo_points.length > 0) {
        const point = redo_points.pop();
        addPoint(point)
    }
}

function updateInterface() {
    
    document.getElementById('undo').style.visibility = selected_points.length === 0 ? 'hidden' : 'visible';
    document.getElementById('redo').style.visibility = redo_points.length === 0 ? 'hidden' : 'visible';
    
    let error_flashes = document.getElementById("section_tracking_form").getElementsByClassName("flashes")[0];
    if (document.body.contains(error_flashes)) {
        error_flashes.parentNode.removeChild(error_flashes);
    }
}

function goBack() {
    selected_points = [];
    redo_points = [];
    history.back();
}
