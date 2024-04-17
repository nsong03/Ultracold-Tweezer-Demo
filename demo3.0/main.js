var playing = true;
var whichsim = 0;
var currentrunnum = 0
var currentframenum = 0
var slides = document.querySelectorAll('.slide');
slides.forEach(function(slide) {
    slide.classList.remove('active');
});




function fetchFrame() {
    fetch('/stream')
        .then(response => response.json())
        .then(data => {
            currentframenum = data.currentframenumber
            currentrunnum = data.currentrunnum
            displayFrame(currentframenum, whichsim);
            

            if (playing) {
                fetchFrame();
                var activeSlideId;
                if (whichsim === 0){
                    if (currentframenum >= 0 && currentframenum < 1) {
                        activeSlideId = '0welcome'; // Show first slide
                    } else if (currentframenum >= 1 && currentframenum < 170) {
                        activeSlideId = '1atomsload'; // Show second slide
                    } else if (currentframenum >= 170 && currentframenum < 359) {
                        activeSlideId = '2sortatoms'; // Show third slide
                    } else if (currentframenum >= 359 && currentframenum < 360) {
                        activeSlideId = '3atomssorted'; // Show third slide
                    } else if (currentframenum >= 360 && currentframenum < 411) {
                        activeSlideId = '4atomsresorted'; // Show third slide
                    } else if (currentframenum >= 411 && currentframenum <= 487) {
                        activeSlideId = '5shuttingdown'; // Show third slide
                    }
                }
                else if (whichsim === 1) {
                    if (currentframenum >= 0 && currentframenum < 1) {
                        activeSlideId = '0welcome'; // Show first slide
                    } else if (currentframenum >= 1 && currentframenum < 281) {
                        activeSlideId = '1atomsload'; // Show second slide
                    } else if (currentframenum >= 281 && currentframenum < 282) {
                        activeSlideId = '3atomssorted'; // Show third slide
                    } else if (currentframenum >= 283 && currentframenum < 411) {
                        activeSlideId = '4atomsresorted'; // Show third slide
                    } else if (currentframenum >= 411) {
                        activeSlideId = '5shuttingdown'; // Show third slide
                    }
                }

                var slides = document.querySelectorAll('.slide');
                slides.forEach(function(slide) {
                    slide.classList.remove('active');
                });
                var activeSlide = document.getElementById(activeSlideId);
                activeSlide.classList.add('active');

                var runnumDisplay = document.getElementById('currentrun');
                runnumDisplay.textContent = 'Simulation Active. Current Run: ' + currentrunnum
                if (whichsim === 0) {
                    var slmphaseimgurl = `/slmzoomedphases/zoomed_${currentframenum}.jpg`;  // Adjust the URL pattern as needed

                }
                else if (whichsim === 1){
                    var slmphaseimgurl = `/zoomedslmphases1d/phaseimg${currentframenum}.jpg`;  // Adjust the URL pattern as needed

                }
                var slmphaseDisplay = document.getElementById('slmphasedisplay');
                slmphaseDisplay.src = slmphaseimgurl;


            }
        })
        .catch(error => console.error('Error fetching frame:', error));
}

function displayFrame(currentframenum, whichsim) {
    // const canvas = document.getElementById('canvas');
    // const ctx = canvas.getContext('2d');

    // if (frame !== null) {
    //     const gridSize = 2; // Adjust grid size if needed
    //     canvas.width = frame[0].length * gridSize;
    //     canvas.height = frame[1].length * gridSize;
        
    //     ctx.fillStyle = 'black';
    //     ctx.fillRect(0, 0, canvas.width, canvas.height);

    //     ctx.fillStyle = 'white';
    //     frame.forEach((row, rowIndex) => {
    //         row.forEach((cell, colIndex) => {
    //             if (cell == 1){
    //                 ctx.fillRect(colIndex * gridSize, rowIndex * gridSize, gridSize, gridSize);
    //             }
                
    //         });
    //     });((n % d) + d) % d
    // }
    if (currentframenum-1 < 0 && whichsim === 0) {
        var fullsimmovieurl =  `/fullsimmovie2dgauss/array_${485}.jpg`;
        var fullsimmovie = document.getElementById('fullsimmovie');
        fullsimmovie.src = fullsimmovieurl;
    }
    else if (whichsim === 0) {
        var fullsimmovieurl =  `/fullsimmovie2dgauss/array_${(currentframenum-1)%486}.jpg`;
        var fullsimmovie = document.getElementById('fullsimmovie');
        fullsimmovie.src = fullsimmovieurl;
    }
    else if (currentframenum - 1 < 0 && whichsim === 1) {
        var fullsimmovieurl =  `/fullsimmovie1d/array_${581}.jpg`;
        var fullsimmovie = document.getElementById('fullsimmovie');
        fullsimmovie.src = fullsimmovieurl;
    }
    else if (whichsim === 1) {
        var fullsimmovieurl =  `/fullsimmovie1d/array_${(currentframenum-1)%582}.jpg`;
        var fullsimmovie = document.getElementById('fullsimmovie');
        fullsimmovie.src = fullsimmovieurl;
    }


}




function togglePlayPause() {
    playing = !playing
    if (playing) {
        playPauseBtn.style.backgroundImage = 'url(playbutton.jpg)';
        fetchFrame();
        // Add code here to resume playback or trigger fetching frames
    } else {
        playPauseBtn.style.backgroundImage = 'url(pausebutton.jpg)';
        // Add code here to pause playback or stop fetching frames
    }
    updateServerValues();


}

function toggleBoldText() {
    whichsim = (whichsim + 1) % 2
    currentframenum = 2
    const text1D = document.getElementById('text1D');
    const text2D = document.getElementById('text2D');
    if (whichsim == 0){
        text1D.style.fontWeight = 'normal';
        text2D.style.fontWeight = 'bold';
    }
    if (whichsim == 1){
        text1D.style.fontWeight = 'bold';
        text2D.style.fontWeight = 'normal';
    }

    updateServerValues();
    togglePlayPause();
    fetchFrame();
}

function updateServerValues() {
    var data = { playing: playing, whichsim: whichsim };
    // Send AJAX POST request to update_values endpoint
    fetch('/update_values', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        console.log('Values updated on server');
    })
    .catch(error => console.error('Error updating values:', error));
}


document.addEventListener('DOMContentLoaded', function () {


    // Get the play/pause button element
    const playPauseBtn = document.getElementById('playPauseBtn');
    playPauseBtn.addEventListener('click', togglePlayPause);


    const displayToggleBtn = document.getElementById('displaytoggleButton');
    displayToggleBtn.addEventListener('click', toggleBoldText);
});



// Initial fetch frame

togglePlayPause();
toggleBoldText();
fetchFrame();




