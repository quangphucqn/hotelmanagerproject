// animation.js

document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("snowfall");
    for (let i = 0; i < 100; i++) {
        const flake = document.createElement("div");
        flake.style.left = Math.random() * window.innerWidth + "px";
        flake.style.animationDelay = Math.random() * 5 + "s";
        flake.style.animationDuration = Math.random() * 5 + 5 + "s";
        container.appendChild(flake);
    }
});
