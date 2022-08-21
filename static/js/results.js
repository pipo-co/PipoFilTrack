"use strict";

class ResultsViewer {

    constructor() {
        this.frames = [];
        this.index = 0;
        this.loop = true;
        this.inter_id = null;
        this.fps = 1;

        this.canvas = document.createElement('canvas');
        this.canvas.classList.add('canvas');

        this.controls = {};
    }

    bindViewer(bindElement) {
        bindElement.appendChild(this.canvas);

        const resultControls = document.getElementById('result-controlls').content.cloneNode(true);
        bindElement.appendChild(resultControls);

        this.controls['loop']               = document.getElementById('rc-loop');
        this.controls['frame']              = document.getElementById('rc-frame');
        this.controls['play']               = document.getElementById('rc_play');
        this.controls['stop']               = document.getElementById('rc_stop');
        this.controls['next_frame']         = document.getElementById('rc_next_frame');
        this.controls['prev_frame']         = document.getElementById('rc_prev_frame');
        this.controls['frame_rate_up']      = document.getElementById('rc_frame_rate_up');
        this.controls['frame_rate_down']    = document.getElementById('rc_frame_rate_down');
        this.controls['frame_rate']         = document.getElementById('rc_frame_rate_value');

        this.controls['loop'].addEventListener('click', rcLoop);
        this.controls['play'].addEventListener('click', () => this.resumeAnimation());
        this.controls['stop'].addEventListener('click', () => this.stopAnimation());
        this.controls['next_frame'].addEventListener('click', () => this.drawNextFrame());
        this.controls['prev_frame'].addEventListener('click', () => this.drawPrevFrame());
        this.controls['frame_rate_up'].addEventListener('click', () => this.updateFrameRate(1));
        this.controls['frame_rate_down'].addEventListener('click', () => this.updateFrameRate(-1));
    }

    setResolution(width, height) {
        this.canvas.width = 1000; //TODO(nacho)
        this.canvas.height = this.canvas.width / width * height;
    }

    loadResults(frames) {
        this.frames = frames
        
        this.setResolution(frames[0].width, frames[0].height);

        this.drawFrame();
        this.updateFrameRateNumberDisplay();
        // this.resumeAnimation();
    }

    resumeAnimation() {
        this.pauseAnimation();

        this.inter_id = setInterval(() => this.animationHandler(), 1000 / this.fps);
    }

    pauseAnimation() {
        if(this.inter_id) {
            clearInterval(this.inter_id);
        }
    }

    updateFrameRate(delta) {
        console.log(this.fps, delta, Math.max(this.fps + delta, 1))
        this.fps = Math.max(this.fps + delta, 1);
        this.resumeAnimation();
        this.updateFrameRateNumberDisplay();
    }

    animationHandler() {
        if(!this.loop && this.index == this.frames.length-1) {
            clearInterval(this.inter_id)
            this.inter_id = null
            return
        }
        this.drawNextFrame();
    }

    updateFrameNumberDisplay() {
        this.controls['frame'].innerHTML = `${this.index+1}/${this.frames.length}`
    }

    updateFrameRateNumberDisplay() {
        this.controls['frame_rate'].innerHTML = `${this.fps} fps`
    }

    nextFrame() {
        if(this.loop) {
            this.index = (this.index + 1) % this.frames.length;
        } else {
            this.index = Math.min(this.index + 1, this.frames.length - 1);
        }
    }

    prevFrame() {
        this.index = Math.max(this.index - 1, 0);
    }

    drawFrame() {
        this.controls['frame'].innerHTML = `${this.index+1}/${this.frames.length}`
        drawIntoCanvas(this.canvas, this.frames[this.index]);
    }

    drawNextFrame() {
        console.log("Next");
        this.nextFrame();
        this.drawFrame();
    }

    drawPrevFrame() {
        console.log("Preev");
        this.prevFrame();
        this.drawFrame();
    }
    
    stopAnimation() {
        this.pauseAnimation()
        this.index = 0
        this.drawFrame();
    }
}