// // Get video element and capture button
// const video = document.getElementById('video');
// const captureButton = document.getElementById('capture');
// const canvas = document.getElementById('canvas');

// // Access user's webcam
// navigator.mediaDevices.getUserMedia({ video: true })
//   .then(stream => {
//     video.srcObject = stream;
//   })
//   .catch(error => {
//     console.error("Error accessing webcam: ", error);
//   });

// // Capture image from the webcam
// captureButton.addEventListener('click', function() {
//   const context = canvas.getContext('2d');
//   canvas.width = video.videoWidth;
//   canvas.height = video.videoHeight;
//   context.drawImage(video, 0, 0, canvas.width, canvas.height);

//   // Convert the canvas to a data URL (image)
//   const imageDataURL = canvas.toDataURL('image/png');
//   console.log("Captured image: ", imageDataURL);

//   // You can send the captured image to the server for face recognition here.
// });
