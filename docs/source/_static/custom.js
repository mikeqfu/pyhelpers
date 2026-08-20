document.addEventListener("DOMContentLoaded", function() {

    // Function to add a styled colon after specific headers
    function addStyledColonAfterHeaders(headers, headerTexts) {
        headers.forEach(function(header) {
            if (header && header.nextSibling && header.nextSibling.nodeType === Node.TEXT_NODE &&
                    header.nextSibling.textContent.trim() === ":") {
                header.parentNode.removeChild(header.nextSibling);
            }
            if (headerTexts.includes(header.textContent.trim())) {
                let colonSpan = document.createElement("span");
                colonSpan.textContent = ":";
                colonSpan.classList.add("examples-colon"); // Optional: Add a class for styling
                header.parentNode.insertBefore(colonSpan, header.nextSibling);
            }
        });
    }

    // Apply the function to the examples headers
    let examplesHeaders = document.querySelectorAll("p > strong");
    addStyledColonAfterHeaders(examplesHeaders, ["Examples", "Illustration", "Define a proxy object that inherits from this class"]);

    // Add a colon to rubric paragraphs
    let rubricParagraphs = document.querySelectorAll("p.rubric");
    rubricParagraphs.forEach(function(paragraph) {
        if (!paragraph.textContent.trim().endsWith(":")) {
            paragraph.textContent = paragraph.textContent.trim() + ":";
        }
    });

    // Make external links open in new tab
    let links = document.querySelectorAll('a.external');
    links.forEach(function(link) {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });

    // Find the footer element
    const footerLeft = document.querySelector('.left-details');
    if (!footerLeft) return;

    // Find the "Made with" text
    const madeWithText = footerLeft.textContent || '';
    if (madeWithText.includes('Made with')) {
        // Get the copyright div
        const copyrightDiv = footerLeft.querySelector('.copyright');

        // Clear everything after the copyright div
        while (copyrightDiv.nextSibling) {
            copyrightDiv.nextSibling.remove();
        }

        // Add our custom text
        const customText = document.createElement('span');
        customText.innerHTML = ' Created using ' +
            '<a href="https://www.sphinx-doc.org/" target="_blank">Sphinx</a> and ' +
            '<a href="https://github.com/pradyunsg/furo" target="_blank">Furo</a>';
        footerLeft.appendChild(customText);
    }
});
