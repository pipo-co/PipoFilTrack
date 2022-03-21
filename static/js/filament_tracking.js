let pointSize = 4;
let undo_points = [];
let redo_points = [];

$(document).ready(function () {
    $("#canvas").click(function(e){
         getPosition(e);
    });

    $("#plus").click(function(e){
         increaseDotSize(e);
    });

    $("#minus").click(function(e){
         decreaseDotSize(e);
    });

    $("#undo").click(function(e){
         undoPoint(e);
    });

    $("#redo").click(function(e){
         redoPoint(e);
    });

    $("#submit_tracking_form").click(function (e){
       e.preventDefault();
       if (undo_points.length !== 2) {
           $("#section_tracking_form").append(
               "<div class=\"flashes mt-2\"><p>Debe seleccionar el punto inicial y final del filamento</p></div>"
           );
       } else {
           $('#toggle_filter').prop('checked',false);
           $("#tracking_form").submit();
       }

    });

    $('#toggle_filter').change(function() {
        if ($('#toggle_filter').prop('checked')) {
            document.getElementById('canvas').style.background = document.getElementById('canvas').style.background.replace('.jpg', 'filter.jpg');
        } else {
            document.getElementById('canvas').style.background = document.getElementById('canvas').style.background.replace('filter.jpg', '.jpg');
        }
    })

    function getPosition(event){
        if (undo_points.length < 2) {
            let rect = canvas.getBoundingClientRect();
            let x = event.clientX - rect.left;
            let y = event.clientY - rect.top;
            undo_points.push({'x': x, 'y': y});
            updatePoints();

            drawCoordinates(x,y);
            updatePointSizeInForm();
        }
    }

    function drawCoordinates(x,y){
        let canvas = document.getElementById("canvas");
        let ctx = canvas.getContext("2d");

        if (canvas.width !== canvas.clientWidth) {
            document.getElementById("canvas_size").value = JSON.stringify(0.74 * window.innerHeight);
            canvas.width = canvas.clientWidth;
            canvas.height = canvas.clientHeight;
        }

        ctx.fillStyle = "#ff0000";

        ctx.beginPath();
        ctx.arc(x, y, pointSize, 0, Math.PI * 2, true);
        ctx.fill();
    }

    function increaseDotSize() {
        pointSize += 0.5;
    }

    function decreaseDotSize() {
        pointSize -= 0.5;
    }

    function updatePointSizeInForm() {
        let formTrack = document.forms['tracking_form'];
        formTrack.point_size.value = pointSize;
    }

    function undoPoint(){
        let ctx = document.getElementById("canvas").getContext("2d");
        const size = 0.74 * window.innerHeight;

        if (undo_points.length > 0) {
            redo_points.push(undo_points.pop());
            ctx.clearRect(0, 0, size, size);
            undo_points.forEach(function redraw(currentValue) {
                drawCoordinates(currentValue['x'], currentValue['y']);
            })
            updatePoints();
        }
    }

    function redoPoint(){
        if (redo_points.length > 0) {
            undo_points.push(redo_points.pop());
            drawCoordinates(undo_points[undo_points.length-1]['x'], undo_points[undo_points.length-1]['y']);
            updatePoints();
        }
    }

    function updatePoints() {
        document.getElementById("points").value = JSON.stringify(undo_points);
        if (undo_points.length === 0) {
           document.getElementById('undo').getElementsByTagName('img')[0].style.visibility = "hidden";
        } else {
            document.getElementById('undo').getElementsByTagName('img')[0].style.visibility = "visible";
        }
        if (redo_points.length === 0 || undo_points.length === 2) {
           document.getElementById('redo').getElementsByTagName('img')[0].style.visibility = "hidden";
        } else {
            document.getElementById('redo').getElementsByTagName('img')[0].style.visibility = "visible";
        }
        if (undo_points.length === 2) {
            document.getElementById("canvas").style.cursor = "default";
        } else {
            document.getElementById("canvas").style.cursor = "crosshair";
        }

        let error_flashes = document.getElementById("section_tracking_form").getElementsByClassName("flashes")[0];
        if (document.body.contains(error_flashes)) {
            error_flashes.parentNode.removeChild(error_flashes);
        }
    }

    const totalItems = $('#carouselControls .carousel-item').length;
    $('#carouselControls').on('slid.bs.carousel', function() {
        currentIndex = $('#carouselControls div.active').index() + 1;
        $('.frame_index').html('' + currentIndex + ' / ' + totalItems + '');
    });
});

function goBack() {
    pointSize = 4;
    undo_points = [];
    redo_points = [];
    history.back();
}

function pauseCarousel() {
    console.log('pauseCarousel')
    $('#carouselControls').carousel('pause');
}
