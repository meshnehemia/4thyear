    // // Get elements from DOM
    // const video = document.getElementById('video');
    // const captureBtn = document.getElementById('capture');

    // // Prompt user to grant access to webcam
    // navigator.mediaDevices.getUserMedia({ video: true })
    //   .then((stream) => {
    //     video.srcObject = stream;
    //   })
    //   .catch((err) => {
    //     console.error("Error accessing the camera: " + err);
    //   });

    // // Capture button functionality
    // captureBtn.addEventListener('click', function() {
    //   const canvas = document.createElement('canvas');
    //   const context = canvas.getContext('2d');
    //   canvas.width = video.videoWidth;
    //   canvas.height = video.videoHeight;
    //   context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
    //   // Show captured image (optional)
    //   const imageDataURL = canvas.toDataURL('image/png');
    //   console.log("Captured image: ", imageDataURL);
      
    //   // Here you can send the image to the server or use face recognition logic
    // });
