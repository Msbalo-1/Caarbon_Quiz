document.addEventListener("DOMContentLoaded", function () {
    // Show a message when user levels up
    function showMessage(message) {
        alert(message);  // Temporary alert for demonstration; could be replaced with a styled modal.
    }





    // Handle answer selection and calculate points
    document.querySelectorAll('.answer-btn').forEach(button => {
        button.addEventListener('click', function () {
            const isCorrect = button.dataset.correct === "true";
            const levelUpPoints = 10; // Points needed for level-up

            if (isCorrect) {
                showMessage("Correct! +5 points awarded.");
                updatePoints(5);
            } else {
                showMessage("Try again! Incorrect answer.");
                updatePoints(4); // Award 4 points on retry if incorrect initially
            }

            checkForLevelUp(levelUpPoints);
        });
    });

    // Update points dynamically in the UI (points may be reloaded from server if necessary)
    function updatePoints(points) {
        const pointsDisplay = document.querySelector("#points-display");
        let currentPoints = parseInt(pointsDisplay.innerText) || 0;
        currentPoints += points;
        pointsDisplay.innerText = currentPoints;
    }

    // Check if user qualifies to level up
    function checkForLevelUp(levelUpPoints) {
        const currentPoints = parseInt(document.querySelector("#points-display").innerText);
        if (currentPoints >= levelUpPoints) {
            showMessage("Congratulations! You've leveled up.");
            loadNextLevel();
        }
    }

    // Load next level - replace with a server call or page navigation as needed
    function loadNextLevel() {
        // Sample navigation or reloading with next level.
        window.location.href = "/play/next-level";  // This URL needs to be defined in app routes
    }

    // Pause and quit buttons
    document.querySelector("#pause-btn").addEventListener("click", function () {
        showMessage("Game paused. Click OK to continue.");
    });

    document.querySelector("#quit-btn").addEventListener("click", function () {
        if (confirm("Are you sure you want to quit?")) {
            window.location.href = "/";  // Navigate back to the home page
        }
    });

    // Toggle category levels
    document.querySelectorAll(".category").forEach(category => {
        category.addEventListener("click", function () {
            const levelDropdown = category.querySelector(".levels-dropdown");
            levelDropdown.classList.toggle("show");
        });
    });
});

// Responsive adjustments (for mobile view)
window.addEventListener("resize", function () {
    const isMobile = window.innerWidth < 768;
    adjustUIForMobile(isMobile);
});

function adjustUIForMobile(isMobile) {
    if (isMobile) {
        document.body.style.fontSize = "14px";  // Example mobile adjustment
    } else {
        document.body.style.fontSize = "16px";
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const ratingInput = document.querySelector('#rating');
    ratingInput.addEventListener('input', () => {
        if (ratingInput.value > 5) {
            ratingInput.value = 5;
        }
        if (ratingInput.value < 1) {
            ratingInput.value = 1;
        }
    });
});






