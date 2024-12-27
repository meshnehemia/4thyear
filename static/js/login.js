document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureButton = document.getElementById('capture');
    const capturedImageInput = document.getElementById('captured-image');
  
    captureButton.addEventListener('click', () => {
        // Set canvas size equal to video feed size
        canvas.width = video.width;
        canvas.height = video.height;
  
        // Draw the video frame onto the canvas
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
  
        // Convert canvas content to a data URL (image)
        const imageData = canvas.toDataURL('image/png');
  
        // Set the captured image to the hidden input value
        
  
        // Change the canvas display style to block (or inline if preferred)
        canvas.style.display = 'block'; 

        // Send the captured image to the backend for processing
        fetch('/capture_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            if (data.message === 'face detected continue to register') {
                capturedImageInput.value = imageData;
                alert(data.message);
            } else {
                alert('Image not clear. Ensure your face is clear.');
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Form validation before submission
    document.getElementById('login-form').addEventListener('submit', function(event) {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const capturedImageData = capturedImageInput.value;
        event.preventDefault();
        if (!email || !password || !capturedImageData) {
            alert('Please fill out all fields and capture your image.');  // Prevent form submission
            return;
        }
  
        const formData = {
            email: email,
            password: password,
            captured_image_data: capturedImageData
        };
  
        // Send the data using fetch()
        fetch('/signing', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            alert(data.message);
            if(data.message === "Login successful."){
                window.location.href = '/';
            }else{
                
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    });
});
