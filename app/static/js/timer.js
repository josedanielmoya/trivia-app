class GameTimer {
    constructor(totalSeconds, onTimeUp) {
        this.totalSeconds = totalSeconds;
        this.remainingSeconds = totalSeconds;
        this.onTimeUp = onTimeUp;
        this.timerId = null;
        this.startTime = null;
    }

    start() {
        this.startTime = Date.now();
        this.timerId = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            this.remainingSeconds = Math.max(0, this.totalSeconds - elapsed);

            this.updateDisplay();

            if (this.remainingSeconds <= 0) {
                this.stop();
                this.onTimeUp();
            }
        }, 100);
    }

    updateDisplay() {
        const display = document.getElementById('timer-display');
        if (display) {
            display.textContent = this.remainingSeconds;

            // Change color as time runs out
            if (this.remainingSeconds <= 5) {
                display.classList.add('timer-critical');
            } else {
                display.classList.remove('timer-critical');
            }
        }
    }

    stop() {
        if (this.timerId) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
    }

    getRemaining() {
        return this.remainingSeconds;
    }
}

// Initialize on page load
let gameTimer = null;

document.addEventListener('DOMContentLoaded', function() {
    const totalSeconds = parseInt(document.getElementById('timer-display').dataset.seconds);
    gameTimer = new GameTimer(totalSeconds, handleTimeUp);
    gameTimer.start();
});

function handleTimeUp() {
    const form = document.getElementById('answer-form');
    // Select first available option if none selected
    const selected = document.querySelector('input[name="answer"]:checked');
    if (!selected) {
        const firstOption = document.querySelector('input[name="answer"]');
        if (firstOption) {
            firstOption.checked = true;
        }
    }
    form.submit();
}

function submitAnswer() {
    gameTimer.stop();
    const form = document.getElementById('answer-form');
    const selected = document.querySelector('input[name="answer"]:checked');

    if (!selected) {
        alert('Please select an answer!');
        return false;
    }

    // Record time taken
    const timeTaken = gameTimer.totalSeconds - gameTimer.getRemaining();
    const timeInput = document.getElementById('time-taken-input');
    timeInput.value = timeTaken.toString();

    form.submit();
}
