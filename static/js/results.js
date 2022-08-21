"use strict";

class ResultsViewer {
    constructor(templateId) {
        this.templateId = templateId;
        this.canvas     = document.createElement('canvas');
        this.frames     = [];
        this.index      = 0;
        this.inter_id   = null;
        this.fps        = 1;

        this.controls = {};
    }

    bindViewer(bindElement) {
        bindElement.appendChild(this.canvas);

        // TODO(tobi): Porque deep copy?
        const template = document.getElementById(this.templateId);
        bindElement.appendChild(template.content.cloneNode(true));

        this.controls['frame']              = document.getElementById('rc-frame');
        this.controls['play']               = document.getElementById('rc-play');
        this.controls['stop']               = document.getElementById('rc-stop');
        this.controls['next_frame']         = document.getElementById('rc-next_frame');
        this.controls['prev_frame']         = document.getElementById('rc-prev_frame');
        this.controls['frame_rate_up']      = document.getElementById('rc-frame_rate_up');
        this.controls['frame_rate_down']    = document.getElementById('rc-frame_rate_down');
        this.controls['frame_rate']         = document.getElementById('rc-frame_rate_value');

        this.controls['play']           .addEventListener('click', () => this.resumeAnimation());
        this.controls['stop']           .addEventListener('click', () => this.stopAnimation());
        this.controls['next_frame']     .addEventListener('click', () => this.drawNextFrame());
        this.controls['prev_frame']     .addEventListener('click', () => this.drawPrevFrame());
        this.controls['frame_rate_up']  .addEventListener('click', () => this.updateFrameRate(1));
        this.controls['frame_rate_down'].addEventListener('click', () => this.updateFrameRate(-1));
    }

    loadResults(frames) {
        this.frames = frames
        
        setResolution(this.canvas, frames[0].width, frames[0].height);

        this.drawFrame();
        this.updateFrameRateNumberDisplay();
    }

    resumeAnimation() {
        this.pauseAnimation();
        this.inter_id = setInterval(() => this.drawNextFrame(), 1000 / this.fps);
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

    updateFrameNumberDisplay() {
        this.controls['frame'].innerHTML = `${this.index+1}/${this.frames.length}`
    }

    updateFrameRateNumberDisplay() {
        this.controls['frame_rate'].innerHTML = `${this.fps} fps`
    }

    nextFrame() {
        this.index = (this.index + 1) % this.frames.length;
    }

    prevFrame() {
        this.index = this.index === 0 ? this.frames.length - 1 : this.index - 1;
    }

    drawFrame() {
        this.updateFrameNumberDisplay()
        drawIntoCanvas(this.canvas, this.frames[this.index]);
    }

    drawNextFrame() {
        this.nextFrame();
        this.drawFrame();
    }

    drawPrevFrame() {
        this.prevFrame();
        this.drawFrame();
    }
    
    stopAnimation() {
        this.pauseAnimation()
        this.index = 0
        this.drawFrame();
    }
}