// Biometric Platform Frontend Logic
let activeStream = null;
let activeVideoId = null;

// Input method tracking ('webcam' or 'upload')
let regMethod = 'webcam';
let verifyMethod = 'webcam';
let faceIdMethod = 'webcam';
let bodyIdMethod = 'webcam';
let resizeMethod = 'webcam';

// Uploaded base64 image variables
let regUploadBase64 = null;
let verifyUploadBase64 = null;
let faceIdUploadBase64 = null;
let bodyIdUploadBase64 = null;
let resizeUploadBase64 = null;

// Base64 helper for capturing canvas frame
function captureFrame(videoElementId) {
    const video = document.getElementById(videoElementId);
    if (!video || !video.srcObject) return null;
    
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    return canvas.toDataURL('image/jpeg', 0.9);
}

// Camera Management
async function startCamera(videoElementId, fallbackElementId) {
    stopCamera(); // Clean up first
    
    const video = document.getElementById(videoElementId);
    const fallback = document.getElementById(fallbackElementId);
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: "user"
            }
        });
        activeStream = stream;
        activeVideoId = videoElementId;
        video.srcObject = stream;
        if (fallback) fallback.classList.add('hidden');
    } catch (err) {
        console.error("Camera access error:", err);
        if (fallback) {
            fallback.classList.remove('hidden');
            fallback.innerHTML = `<span class="px-4 text-center text-brand-error">Camera Error: ${err.message}. Please allow camera access.</span>`;
        }
    }
}

function stopCamera() {
    if (activeStream) {
        activeStream.getTracks().forEach(track => track.stop());
        activeStream = null;
        if (activeVideoId) {
            const video = document.getElementById(activeVideoId);
            if (video) video.srcObject = null;
            activeVideoId = null;
        }
    }
}

// File Upload Reader Helper
function setupImageUpload(fileInputId, previewId, previewContainerId, promptId, callback) {
    const fileInput = document.getElementById(fileInputId);
    const prompt = document.getElementById(promptId);
    const preview = document.getElementById(previewId);
    const previewContainer = document.getElementById(previewContainerId);

    if (prompt && fileInput) {
        prompt.addEventListener('click', () => fileInput.click());
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    const base64 = event.target.result;
                    if (preview) preview.src = base64;
                    if (previewContainer) previewContainer.classList.remove('hidden');
                    if (prompt) prompt.classList.add('hidden');
                    callback(base64);
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

function resetImageUpload(fileInputId, previewId, previewContainerId, promptId, clearVarCallback) {
    const fileInput = document.getElementById(fileInputId);
    const prompt = document.getElementById(promptId);
    const preview = document.getElementById(previewId);
    const previewContainer = document.getElementById(previewContainerId);

    if (fileInput) fileInput.value = "";
    if (preview) preview.src = "";
    if (previewContainer) previewContainer.classList.add('hidden');
    if (prompt) prompt.classList.remove('hidden');
    clearVarCallback();
}

// File Download Helper
function triggerDownload(dataUrl, filename) {
    const cleanFilename = filename.trim().replace(/[^a-zA-Z0-9_\-]/g, ""); // sanitize
    if (!cleanFilename) {
        alert("Please enter a valid filename.");
        return;
    }
    
    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = cleanFilename + ".jpg";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// UI State Switcher
function showStatus(element, message, type) {
    element.classList.remove('hidden', 'bg-brand-success/10', 'border-brand-success/20', 'text-brand-success', 'bg-brand-error/10', 'border-brand-error/20', 'text-brand-error', 'bg-slate-800/50', 'border-slate-700', 'text-slate-400');
    element.classList.add('block');
    
    if (type === 'success') {
        element.classList.add('bg-brand-success/10', 'border', 'border-brand-success/20', 'text-brand-success');
    } else if (type === 'error') {
        element.classList.add('bg-brand-error/10', 'border', 'border-brand-error/20', 'text-brand-error');
    } else {
        element.classList.add('bg-slate-800/50', 'border', 'border-slate-700', 'text-slate-400');
    }
    element.innerHTML = message;
}

// Document Ready
document.addEventListener('DOMContentLoaded', () => {
    // Initial Session Check
    checkSession();
    
    // Setup File Uploads
    setupImageUpload('regFileInput', 'regUploadPreview', 'regUploadPreviewContainer', 'regUploadPrompt', (base64) => {
        regUploadBase64 = base64;
    });
    setupImageUpload('verifyFileInput', 'verifyUploadPreview', 'verifyUploadPreviewContainer', 'verifyUploadPrompt', (base64) => {
        verifyUploadBase64 = base64;
    });
    setupImageUpload('faceIdFileInput', 'faceIdUploadPreview', 'faceIdUploadPreviewContainer', 'faceIdUploadPrompt', (base64) => {
        faceIdUploadBase64 = base64;
    });
    setupImageUpload('bodyIdFileInput', 'bodyIdUploadPreview', 'bodyIdUploadPreviewContainer', 'bodyIdUploadPrompt', (base64) => {
        bodyIdUploadBase64 = base64;
    });
    setupImageUpload('resizeFileInput', 'resizeUploadPreview', 'resizeUploadPreviewContainer', 'resizeUploadPrompt', (base64) => {
        resizeUploadBase64 = base64;
    });

    // Remove File Upload handlers
    document.getElementById('btnRemoveRegUpload').addEventListener('click', () => {
        resetImageUpload('regFileInput', 'regUploadPreview', 'regUploadPreviewContainer', 'regUploadPrompt', () => { regUploadBase64 = null; });
    });
    document.getElementById('btnRemoveVerifyUpload').addEventListener('click', () => {
        resetImageUpload('verifyFileInput', 'verifyUploadPreview', 'verifyUploadPreviewContainer', 'verifyUploadPrompt', () => { verifyUploadBase64 = null; });
    });
    document.getElementById('btnRemoveFaceIdUpload').addEventListener('click', () => {
        resetImageUpload('faceIdFileInput', 'faceIdUploadPreview', 'faceIdUploadPreviewContainer', 'faceIdUploadPrompt', () => { faceIdUploadBase64 = null; });
    });
    document.getElementById('btnRemoveBodyIdUpload').addEventListener('click', () => {
        resetImageUpload('bodyIdFileInput', 'bodyIdUploadPreview', 'bodyIdUploadPreviewContainer', 'bodyIdUploadPrompt', () => { bodyIdUploadBase64 = null; });
    });
    document.getElementById('btnRemoveResizeUpload').addEventListener('click', () => {
        resetImageUpload('resizeFileInput', 'resizeUploadPreview', 'resizeUploadPreviewContainer', 'resizeUploadPrompt', () => { resizeUploadBase64 = null; });
    });

    // TAB NAVIGATION: Sign Up / Log In
    const tabSignUp = document.getElementById('tabSignUp');
    const tabLogIn = document.getElementById('tabLogIn');
    const signUpForm = document.getElementById('signUpForm');
    const logInForm = document.getElementById('logInForm');
    
    tabSignUp.addEventListener('click', () => {
        tabSignUp.classList.add('text-brand-cyan', 'border-brand-cyan', 'bg-brand-cyan/5');
        tabSignUp.classList.remove('text-slate-400', 'border-transparent');
        tabLogIn.classList.remove('text-brand-cyan', 'border-brand-cyan', 'bg-brand-cyan/5');
        tabLogIn.classList.add('text-slate-400', 'border-transparent');
        signUpForm.classList.remove('hidden');
        signUpForm.classList.add('block');
        logInForm.classList.add('hidden');
        logInForm.classList.remove('block');
        
        // Stop any active camera from other workflows
        stopCamera();
        
        // If webcam method is selected for registration, start the camera
        if (regMethod === 'webcam') {
            startCamera('regVideo', 'regCameraFallback');
        }
    });
    
    tabLogIn.addEventListener('click', () => {
        tabLogIn.classList.add('text-brand-cyan', 'border-brand-cyan', 'bg-brand-cyan/5');
        tabLogIn.classList.remove('text-slate-400', 'border-transparent');
        tabSignUp.classList.remove('text-brand-cyan', 'border-brand-cyan', 'bg-brand-cyan/5');
        tabSignUp.classList.add('text-slate-400', 'border-transparent');
        logInForm.classList.remove('hidden');
        logInForm.classList.add('block');
        signUpForm.classList.add('hidden');
        signUpForm.classList.remove('block');
        
        stopCamera(); // No camera needed for credentials entry
    });

    // Input Toggles (Webcam vs Upload)
    const setupToggle = (btnWebcamId, btnUploadId, camContainerId, uploadContainerId, methodSetter, startCamCallback) => {
        const btnWebcam = document.getElementById(btnWebcamId);
        const btnUpload = document.getElementById(btnUploadId);
        const camContainer = document.getElementById(camContainerId);
        const uploadContainer = document.getElementById(uploadContainerId);

        btnWebcam.addEventListener('click', () => {
            methodSetter('webcam');
            btnWebcam.classList.add('bg-indigo-600', 'text-white');
            btnWebcam.classList.remove('text-slate-400', 'hover:text-slate-200');
            btnUpload.classList.remove('bg-indigo-600', 'text-white');
            btnUpload.classList.add('text-slate-400', 'hover:text-slate-200');
            
            camContainer.classList.remove('hidden');
            uploadContainer.classList.add('hidden');
            
            startCamCallback();
        });

        btnUpload.addEventListener('click', () => {
            methodSetter('upload');
            btnUpload.classList.add('bg-indigo-600', 'text-white');
            btnUpload.classList.remove('text-slate-400', 'hover:text-slate-200');
            btnWebcam.classList.remove('bg-indigo-600', 'text-white');
            btnWebcam.classList.add('text-slate-400', 'hover:text-slate-200');
            
            uploadContainer.classList.remove('hidden');
            camContainer.classList.add('hidden');
            
            stopCamera();
        });
    };

    // Initialize toggles for all modules
    setupToggle('btnToggleRegWebcam', 'btnToggleRegUpload', 'regCameraContainer', 'regUploadContainer', 
        (val) => { regMethod = val; }, 
        () => { startCamera('regVideo', 'regCameraFallback'); }
    );
    setupToggle('btnToggleVerifyWebcam', 'btnToggleVerifyUpload', 'verifyCameraContainer', 'verifyUploadContainer', 
        (val) => { verifyMethod = val; }, 
        () => { startCamera('verifyVideo', 'verifyCameraFallback'); }
    );
    setupToggle('btnToggleFaceIdWebcam', 'btnToggleFaceIdUpload', 'faceIdCameraContainer', 'faceIdUploadContainer', 
        (val) => { faceIdMethod = val; }, 
        () => { startCamera('faceIdVideo', 'faceIdCameraFallback'); }
    );
    setupToggle('btnToggleBodyIdWebcam', 'btnToggleBodyIdUpload', 'bodyIdCameraContainer', 'bodyIdUploadContainer', 
        (val) => { bodyIdMethod = val; }, 
        () => { startCamera('bodyIdVideo', 'bodyIdCameraFallback'); }
    );
    setupToggle('btnToggleResizeWebcam', 'btnToggleResizeUpload', 'resizeCameraContainer', 'resizeUploadContainer', 
        (val) => { resizeMethod = val; }, 
        () => { startCamera('resizeVideo', 'resizeCameraFallback'); }
    );

    // SUBMIT SIGN UP
    const btnSubmitRegister = document.getElementById('btnSubmitRegister');
    const regStatus = document.getElementById('regStatus');
    
    btnSubmitRegister.addEventListener('click', async () => {
        const username = document.getElementById('regUsername').value;
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('regConfirmPassword').value;
        
        if (!username || !password || !confirmPassword) {
            showStatus(regStatus, "Please fill in all credential fields.", "error");
            return;
        }
        if (password !== confirmPassword) {
            showStatus(regStatus, "Passwords do not match.", "error");
            return;
        }
        
        let image = null;
        if (regMethod === 'webcam') {
            image = captureFrame('regVideo');
            if (!image) {
                showStatus(regStatus, "Could not capture webcam frame. Activate webcam.", "error");
                return;
            }
        } else {
            image = regUploadBase64;
            if (!image) {
                showStatus(regStatus, "Please upload an image file first.", "error");
                return;
            }
        }
        
        showStatus(regStatus, "Processing registration and face template extraction...", "loading");
        
        try {
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username,
                    password,
                    confirm_password: confirmPassword,
                    image
                })
            });
            const data = await res.json();
            if (data.success) {
                showStatus(regStatus, data.data.message || "Registration successful! Redirecting to Log In...", "success");
                
                // Clear fields
                document.getElementById('regUsername').value = "";
                document.getElementById('regPassword').value = "";
                document.getElementById('regConfirmPassword').value = "";
                resetImageUpload('regFileInput', 'regUploadPreview', 'regUploadPreviewContainer', 'regUploadPrompt', () => { regUploadBase64 = null; });
                
                // Redirect to Login Tab after 2 seconds
                setTimeout(() => {
                    tabLogIn.click();
                    regStatus.classList.add('hidden');
                }, 2000);
            } else {
                showStatus(regStatus, data.message || "Registration failed.", "error");
            }
        } catch (err) {
            showStatus(regStatus, "Network error. Failed to reach server.", "error");
        }
    });

    // SUBMIT LOGIN
    const btnSubmitLogin = document.getElementById('btnSubmitLogin');
    const loginStatus = document.getElementById('loginStatus');
    
    btnSubmitLogin.addEventListener('click', async () => {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        if (!username || !password) {
            showStatus(loginStatus, "Please enter username and password.", "error");
            return;
        }
        
        showStatus(loginStatus, "Authenticating credentials...", "loading");
        
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (data.success) {
                showStatus(loginStatus, data.data.message || "Authenticated! Opening Dashboard...", "success");
                document.getElementById('loginUsername').value = "";
                document.getElementById('loginPassword').value = "";
                setTimeout(() => {
                    enterDashboard(data.data.username);
                }, 1000);
            } else {
                showStatus(loginStatus, data.message || "Invalid credentials.", "error");
            }
        } catch (err) {
            showStatus(loginStatus, "Network error. Failed to login.", "error");
        }
    });

    // LOGOUT
    document.getElementById('logoutBtn').addEventListener('click', async () => {
        stopCamera();
        await fetch('/api/logout', { method: 'POST' });
        location.reload();
    });

    // DASHBOARD SIDEBAR NAVIGATION
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(i => {
                i.classList.remove('bg-brand-purple', 'text-white', 'shadow-md', 'shadow-brand-purple/15');
                i.classList.add('text-slate-400', 'hover:text-slate-200', 'hover:bg-slate-800/30');
            });
            item.classList.add('bg-brand-purple', 'text-white', 'shadow-md', 'shadow-brand-purple/15');
            item.classList.remove('text-slate-400', 'hover:text-slate-200', 'hover:bg-slate-800/30');
            
            const moduleName = item.getAttribute('data-module');
            
            document.querySelectorAll('.module-view').forEach(view => {
                view.classList.add('hidden');
                view.classList.remove('block');
            });
            
            // Activate target view & conditional camera start
            stopCamera();
            if (moduleName === 'faceVerification') {
                document.getElementById('modFaceVerification').classList.remove('hidden');
                document.getElementById('modFaceVerification').classList.add('block');
                if (verifyMethod === 'webcam') startCamera('verifyVideo', 'verifyCameraFallback');
            } else if (moduleName === 'faceIdentification') {
                document.getElementById('modFaceIdentification').classList.remove('hidden');
                document.getElementById('modFaceIdentification').classList.add('block');
                if (faceIdMethod === 'webcam') startCamera('faceIdVideo', 'faceIdCameraFallback');
            } else if (moduleName === 'bodyIdentification') {
                document.getElementById('modBodyIdentification').classList.remove('hidden');
                document.getElementById('modBodyIdentification').classList.add('block');
                if (bodyIdMethod === 'webcam') startCamera('bodyIdVideo', 'bodyIdCameraFallback');
            } else if (moduleName === 'imageResizing') {
                document.getElementById('modImageResizing').classList.remove('hidden');
                document.getElementById('modImageResizing').classList.add('block');
                if (resizeMethod === 'webcam') startCamera('resizeVideo', 'resizeCameraFallback');
            }
        });
    });

    // --- MODULE 1: FACE VERIFICATION SUBMIT ---
    const btnSubmitVerify = document.getElementById('btnSubmitVerify');
    const verifyResultDisplay = document.getElementById('verifyResultDisplay');
    
    btnSubmitVerify.addEventListener('click', async () => {
        let image = null;
        if (verifyMethod === 'webcam') {
            image = captureFrame('verifyVideo');
            if (!image) {
                verifyResultDisplay.innerHTML = `<p class="text-xs text-brand-error font-medium">Please activate webcam stream.</p>`;
                return;
            }
        } else {
            image = verifyUploadBase64;
            if (!image) {
                verifyResultDisplay.innerHTML = `<p class="text-xs text-brand-error font-medium">Please upload an image file.</p>`;
                return;
            }
        }
        
        verifyResultDisplay.innerHTML = `<p class="text-xs text-slate-400 animate-pulse">Running biometric analysis...</p>`;
        
        try {
            const res = await fetch('/api/verify_face', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image })
            });
            const data = await res.json();
            
            if (data.success) {
                const info = data.data;
                const isVerified = info.verification_status === 'verified';
                const statusClass = isVerified ? 'text-brand-success' : 'text-brand-error';
                const statusIcon = isVerified ? '✅' : '❌';
                const scorePercent = info.similarity_threshold ? `Matching Score: <span class="text-white">${roundSimilarity(info.matched_user, info.verification_status)}</span>` : '';
                
                verifyResultDisplay.innerHTML = `
                    <div class="flex flex-col items-center space-y-4 w-full">
                        <div class="text-4xl">${statusIcon}</div>
                        <div class="text-lg font-bold uppercase tracking-wide ${statusClass}">
                            ${isVerified ? 'Verification Successful' : 'Verification Failed'}
                        </div>
                        <div class="bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-xl text-xs text-slate-400 space-y-1 w-full text-center">
                            <div>Matched Identity: <strong class="text-brand-cyan">${info.matched_user}</strong></div>
                            <div>Verification Threshold: <strong class="text-slate-300">${info.similarity_threshold}</strong></div>
                        </div>
                        
                        ${info.image ? `
                            <div class="w-full rounded-xl overflow-hidden border border-slate-800">
                                <img src="${info.image}" class="w-full object-contain" alt="Biometric Overlay">
                            </div>
                        ` : ''}
                    </div>
                `;
            } else {
                verifyResultDisplay.innerHTML = `
                    <div class="flex flex-col items-center space-y-3 text-center">
                        <div class="text-3xl">⚠️</div>
                        <div class="text-sm font-semibold text-brand-error">Verification Error</div>
                        <p class="text-xs text-slate-500">${data.message || "Failed to process face."}</p>
                    </div>
                `;
            }
        } catch (err) {
            verifyResultDisplay.innerHTML = `<p class="text-xs text-brand-error font-medium">Server communication error.</p>`;
        }
    });

    // Helper to calculate verification details from UI side if required, otherwise show status
    function roundSimilarity(matchedUser, status) {
        if (status === 'verified') {
            return "MATCH (> 0.45)";
        }
        return "NO MATCH (< 0.45)";
    }

    // --- MODULE 2: FACE IDENTIFICATION SUBMIT ---
    const btnSubmitFaceId = document.getElementById('btnSubmitFaceId');
    const faceIdResults = document.getElementById('faceIdResults');
    
    btnSubmitFaceId.addEventListener('click', async () => {
        let image = null;
        if (faceIdMethod === 'webcam') {
            image = captureFrame('faceIdVideo');
            if (!image) {
                faceIdResults.innerHTML = `<p class="text-xs text-brand-error text-center">Please activate webcam stream.</p>`;
                return;
            }
        } else {
            image = faceIdUploadBase64;
            if (!image) {
                faceIdResults.innerHTML = `<p class="text-xs text-brand-error text-center">Please upload an image file.</p>`;
                return;
            }
        }
        
        faceIdResults.innerHTML = `<p class="text-xs text-slate-400 animate-pulse text-center">Detecting faces via YOLO...</p>`;
        
        try {
            const res = await fetch('/api/identify_faces', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image })
            });
            const data = await res.json();
            
            if (data.success) {
                const info = data.data;
                if (info.count === 0) {
                    faceIdResults.innerHTML = `
                        <div class="bg-indigo-950/20 border border-indigo-900/30 text-brand-cyan text-xs font-semibold px-4 py-2.5 rounded-xl text-center">
                            0 Faces Detected
                        </div>
                        <p class="text-xs text-slate-500 italic text-center">No faces found in captured scene.</p>
                    `;
                    return;
                }
                
                let html = `
                    <div class="bg-indigo-950/20 border border-indigo-900/30 text-brand-cyan text-xs font-semibold px-4 py-2.5 rounded-xl text-center">
                        ${info.count} ${info.count === 1 ? 'Face' : 'Faces'} Detected
                    </div>
                `;
                
                info.faces.forEach(face => {
                    html += `
                        <div class="grid grid-cols-[80px_1fr] gap-4 bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl items-center">
                            <img src="${face.image}" class="w-20 h-20 rounded-lg object-cover border border-slate-800" alt="Face crop">
                            <div class="space-y-2">
                                <div class="flex space-x-2">
                                    <input type="text" id="faceFilename_${face.id}" value="person_${face.id}" placeholder="Filename"
                                        class="bg-slate-950 border border-slate-850 focus:border-brand-cyan rounded-lg px-2 py-1 text-xs text-slate-200 outline-none flex-1">
                                    <span class="text-xs text-slate-500 self-center">.jpg</span>
                                </div>
                                <button onclick="downloadFaceCrop('${face.id}', '${face.image}')" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-1 rounded-lg text-xs transition">
                                    Download Crop
                                </button>
                            </div>
                        </div>
                    `;
                });
                faceIdResults.innerHTML = html;
            } else {
                faceIdResults.innerHTML = `<p class="text-xs text-brand-error text-center">${data.message || "Failed to run face detection."}</p>`;
            }
        } catch (err) {
            faceIdResults.innerHTML = `<p class="text-xs text-brand-error text-center">Server processing error.</p>`;
        }
    });

    // --- MODULE 3: BODY IDENTIFICATION SUBMIT ---
    const btnSubmitBodyId = document.getElementById('btnSubmitBodyId');
    const bodyIdResults = document.getElementById('bodyIdResults');
    
    btnSubmitBodyId.addEventListener('click', async () => {
        let image = null;
        if (bodyIdMethod === 'webcam') {
            image = captureFrame('bodyIdVideo');
            if (!image) {
                bodyIdResults.innerHTML = `<p class="text-xs text-brand-error text-center">Please activate webcam stream.</p>`;
                return;
            }
        } else {
            image = bodyIdUploadBase64;
            if (!image) {
                bodyIdResults.innerHTML = `<p class="text-xs text-brand-error text-center">Please upload an image file.</p>`;
                return;
            }
        }
        
        bodyIdResults.innerHTML = `<p class="text-xs text-slate-400 animate-pulse text-center">Detecting persons via YOLO...</p>`;
        
        try {
            const res = await fetch('/api/identify_bodies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image })
            });
            const data = await res.json();
            
            if (data.success) {
                const info = data.data;
                bodyIdResults.innerHTML = `
                    <div class="space-y-4 w-full flex flex-col items-center">
                        <div class="bg-indigo-950/20 border border-indigo-900/30 text-brand-cyan text-xs font-semibold px-4 py-2 rounded-full">
                            Detected count: ${info.count}
                        </div>
                        <div class="rounded-xl overflow-hidden border border-slate-800 w-full shadow-lg">
                            <img src="${info.image}" class="w-full object-contain" alt="Annotated scene">
                        </div>
                    </div>
                `;
            } else {
                bodyIdResults.innerHTML = `<p class="text-xs text-brand-error text-center">${data.message || "Failed to process scene."}</p>`;
            }
        } catch (err) {
            bodyIdResults.innerHTML = `<p class="text-xs text-brand-error text-center">Server communication error.</p>`;
        }
    });

    // --- MODULE 4: IMAGE RESIZING SUBMIT ---
    const btnSubmitResize = document.getElementById('btnSubmitResize');
    const resizeResults = document.getElementById('resizeResults');
    
    btnSubmitResize.addEventListener('click', async () => {
        let image = null;
        if (resizeMethod === 'webcam') {
            image = captureFrame('resizeVideo');
            if (!image) {
                resizeResults.innerHTML = `<p class="text-xs text-brand-error text-center">Please activate webcam stream.</p>`;
                return;
            }
        } else {
            image = resizeUploadBase64;
            if (!image) {
                resizeResults.innerHTML = `<p class="text-xs text-brand-error text-center">Please upload an image file.</p>`;
                return;
            }
        }
        
        const wVal = parseInt(document.getElementById('resizeWidth').value);
        const hVal = parseInt(document.getElementById('resizeHeight').value);
        
        if (isNaN(wVal) || isNaN(hVal) || wVal <= 0 || hVal <= 0) {
            alert("Please enter valid width and height values.");
            return;
        }
        
        // Safety dimension guideline check (original webcam aspect is 640x480)
        const minW = 640 * 0.5;
        const maxW = 640 * 2.0;
        const minH = 480 * 0.5;
        const maxH = 480 * 2.0;
        
        if (wVal < minW || wVal > maxW || hVal < minH || hVal > maxH) {
            const proceed = confirm(
                `Warning: The entered dimensions (${wVal}x${hVal}) are outside the recommended scaling range.\n\n` +
                `Recommended dimensions (based on 640x480 standard):\n` +
                `- Width: ${minW} to ${maxW} px\n` +
                `- Height: ${minH} to ${maxH} px\n\n` +
                `Excessive resizing may cause significant pixelation or loss of visibility.\n\n` +
                `Do you want to proceed anyway?`
            );
            if (!proceed) return;
        }
        
        resizeResults.innerHTML = `<p class="text-xs text-slate-400 animate-pulse text-center">Resizing image...</p>`;
        
        try {
            const res = await fetch('/api/resize_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image,
                    width: wVal,
                    height: hVal
                })
            });
            const data = await res.json();
            
            if (data.success) {
                const info = data.data;
                resizeResults.innerHTML = `
                    <div class="flex flex-col items-center space-y-4 w-full">
                        <div class="border border-slate-800 rounded-xl overflow-hidden max-h-[300px] overflow-auto bg-black">
                            <img src="${info.image}" class="max-w-full h-auto block" alt="Resized image">
                        </div>
                        <div class="bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-xl text-[10px] text-slate-500 space-y-1 w-full text-center">
                            <div>Original: ${info.original_width}x${info.original_height} px</div>
                            <div>Resized output: ${info.resized_width}x${info.resized_height} px</div>
                        </div>
                        <div class="flex space-x-2 w-full">
                            <input type="text" id="resizedFilename" value="resized_photo" placeholder="File name"
                                class="bg-slate-950 border border-slate-850 focus:border-brand-cyan rounded-lg px-2 py-1 text-xs text-slate-200 outline-none flex-1">
                            <span class="text-xs text-slate-500 self-center">.jpg</span>
                        </div>
                        <button onclick="downloadResizedImage('${info.image}')" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 rounded-xl text-xs transition">
                            Download Resized Image
                        </button>
                    </div>
                `;
            } else {
                resizeResults.innerHTML = `<p class="text-xs text-brand-error text-center">${data.message || "Failed to resize image."}</p>`;
            }
        } catch (err) {
            resizeResults.innerHTML = `<p class="text-xs text-brand-error text-center">Server processing error.</p>`;
        }
    });
});

// Global triggers for dynamic HTML buttons
window.downloadFaceCrop = (id, imageBase64) => {
    const input = document.getElementById(`faceFilename_${id}`);
    const filename = input ? input.value : `person_${id}`;
    triggerDownload(imageBase64, filename);
};

window.downloadResizedImage = (imageBase64) => {
    const input = document.getElementById("resizedFilename");
    const filename = input ? input.value : "resized_photo";
    triggerDownload(imageBase64, filename);
};

// Enter Dashboard UI
function enterDashboard(username) {
    stopCamera();
    
    document.getElementById('authPanel').classList.add('hidden');
    document.getElementById('dashboardPanel').classList.remove('hidden');
    
    document.getElementById('userStatusHeader').classList.remove('hidden');
    document.getElementById('userStatusHeader').classList.add('flex');
    
    document.getElementById('activeUsername').innerText = username;
    document.getElementById('sidebarUsername').innerText = username;
    
    // Auto click on default module Face Verification to activate it cleanly
    const verifyNavBtn = document.querySelector('[data-module="faceVerification"]');
    if (verifyNavBtn) verifyNavBtn.click();
}

// Check session
async function checkSession() {
    try {
        const res = await fetch('/api/check_session');
        const data = await res.json();
        if (data.success && data.data.logged_in) {
            enterDashboard(data.data.username);
        }
    } catch (err) {
        console.error("Session check failed:", err);
    }
}
