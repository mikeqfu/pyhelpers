// Change font weight for the colon following "Examples" (or "Illustration")
document.addEventListener("DOMContentLoaded", function() {

    var examplesHeaders = document.querySelectorAll("p > strong");

    examplesHeaders.forEach(function(header) {
        if (header && header.nextSibling && header.nextSibling.nodeType === Node.TEXT_NODE &&
                header.nextSibling && header.nextSibling.textContent.trim() === ":") {
            header.parentNode.removeChild(header.nextSibling);
        }
        if (header.textContent.trim() === "Examples" || header.textContent.trim() === "Illustration") {
            var colonSpan = document.createElement("span");
            colonSpan.textContent = ":";
            colonSpan.classList.add("examples-colon"); // Optional: Add a class for styling
            header.parentNode.insertBefore(colonSpan, header.nextSibling);
        }
    });

});
