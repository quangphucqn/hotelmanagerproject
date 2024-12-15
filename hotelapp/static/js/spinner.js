document.addEventListener("DOMContentLoaded", function() {
    var loadingScreen = document.getElementById("loading-screen");
    var mainContent = document.getElementById("main-content");

    setTimeout(function() {
        loadingScreen.style.display = "none";
        mainContent.style.display = "block";
    }, 2000);
});
