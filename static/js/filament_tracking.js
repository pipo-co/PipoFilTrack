const POINT_SIZE = 4;
const POINT_COLOR = '#ff0000';
let selected_points = [];
let redo_points = [];

const form = document.getElementById('tracking_form')
const canvas = document.getElementById('canvas');
const toggle = document.getElementById('toggle_filter');

const images = {}

window.addEventListener('load', () => {

    // clientWidth = width + padding horizontal.
    // Por defecto, si canvas no tiene seteado width usa 300
    document.getElementById('canvas_shape').value = JSON.stringify({width: canvas.clientWidth, height: canvas.clientHeight});
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;

    const image_datalist = document.getElementById('image_urls');
    for (let option of image_datalist.options) {
        images[option.value] = option.text;
    }

    canvas.addEventListener('click', addPoint);

    document.getElementById('undo').addEventListener('click', undoPoint);

    document.getElementById('redo').addEventListener('click', redoPoint);

    form.addEventListener('submit', formSubmitHandler);

    toggle.addEventListener('change', () => {

        log.console('change');
        // $('#toggle_filter').change(function() {
        // if ($('#toggle_filter').prop('checked')) {
        //     document.getElementById('canvas').style.background = document.getElementById('canvas').style.background.replace('.jpg', 'filter.jpg');
        // } else {
        //     document.getElementById('canvas').style.background = document.getElementById('canvas').style.background.replace('filter.jpg', '.jpg');
        // }
        // });
    })
    toggle.addEventListener('click', () => {

        log.console('click');
    })

});

function formSubmitHandler() {

        if (selected_points.length !== 2) {
            const div = document.createElement('div');
            div.className = 'flashes mt-2';
            div.innerHTML = '<p>Debe seleccionar el punto inicial y final del filamento</p>';
            document.getElementById('section_tracking_form').appendChild(div);
            ev.preventDefault();
            return;
        }

        form['points'] = JSON.stringify(selected_points);
        form.submit();
}

function addPoint(event){

    let rect = canvas.getBoundingClientRect();
    let x = event.clientX - rect.left;
    let y = event.clientY - rect.top;
    selected_points.push({'x': x, 'y': y});
    
    updateInterface();
    drawPoint(x,y);
}

function drawPoint(x,y){

    let ctx = canvas.getContext("2d");

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
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Redraw all poins
        selected_points.forEach(function redraw(currentValue) {
            drawPoint(currentValue['x'], currentValue['y']);
        })
        updateInterface();
    }
}

function redoPoint(){
    if (redo_points.length > 0) {
        const point = redo_points.pop();
        selected_points.push(point);
        drawPoint(point['x'], point['y']);
        updateInterface();
    }
}

function updateInterface() {
    
    // debugger;
    document.getElementById('undo').style.visibility = selected_points.length === 0 ? 'hidden' : 'visible';
    document.getElementById('redo').style.visibility = redo_points.length === 0 ? 'hidden' : 'visible';
    
    // document.getElementById('undo').getElementsByTagName('img')[0].style.visibility = "visible";
    
    let error_flashes = document.getElementById("section_tracking_form").getElementsByClassName("flashes")[0];
    if (document.body.contains(error_flashes)) {
        error_flashes.parentNode.removeChild(error_flashes);
    }
}

// $(document).ready(function () {

//     $('#toggle_filter').change(function() {
//         if ($('#toggle_filter').prop('checked')) {
//             document.getElementById('canvas').style.background = document.getElementById('canvas').style.background.replace('.jpg', 'filter.jpg');
//         } else {
//             document.getElementById('canvas').style.background = document.getElementById('canvas').style.background.replace('filter.jpg', '.jpg');
//         }
//     })


//     const totalItems = $('#carouselControls .carousel-item').length;
//     $('#carouselControls').on('slid.bs.carousel', function() {
//         currentIndex = $('#carouselControls div.active').index() + 1;
//         $('.frame_index').html('' + currentIndex + ' / ' + totalItems + '');
//     });
// });

function goBack() {
    selected_points = [];
    redo_points = [];
    history.back();
}

function pauseCarousel() {
    console.log('pauseCarousel')
    $('#carouselControls').carousel('pause');
}
