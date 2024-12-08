document.addEventListener('DOMContentLoaded', function () {
    // SEO Form Handling
    const form = document.getElementById('seo-form');
    const inputField = document.getElementById('website-name');
    const loader = document.getElementById('loader');
    const resultDiv = document.getElementById('result');

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const websiteUrl = inputField.value.trim();
        if (websiteUrl) {
            loader.style.display = 'block';

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: websiteUrl }),
                });

                const data = await response.json();
                loader.style.display = 'none';

                if (data.status === 'success') {
                    const queryParams = new URLSearchParams({
                        title: data.title,
                        meta_description: data.meta_description,
                        h1_count: data.h1_count,
                        canonical_url: data.canonical_url,
                        title_suggestion: data.title_suggestion,
                        meta_description_suggestion: data.meta_description_suggestion,
                        mobile_friendly: data.mobile_friendly
                    }).toString();
                    window.location.href = `/results?${queryParams}`;
                } else {
                    if (data.status === 'error' && data.suggestions) {
                        resultDiv.innerHTML = `<h2>Error:</h2><p>${data.message}</p><h3>Suggestions:</h3><ul>`;
                        data.suggestions.forEach(suggestion => {
                            resultDiv.innerHTML += `<li>${suggestion}</li>`;
                        });
                        resultDiv.innerHTML += '</ul>';
                    } else {
                        resultDiv.innerHTML = `<h2>Error:</h2><p>${data.message}</p>`;
                    }
                }
            } catch (error) {
                loader.style.display = 'none';
                console.error("Error:", error); //Error handler
                alert('Error: Could not connect to the server.');
            }
        } else {
            alert('Please enter a website URL!');
        }
    });

    // Contact Form for WhatsApp
    const contactForm = document.getElementById('contact-form');
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const name = document.getElementById('name').value;
        const message = document.getElementById('message').value;

        const phoneNumber = '+6288740303480';  
        const whatsappMessage = `Hello, my name is ${name}. Message: ${message}`;

        const whatsappLink = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(whatsappMessage)}`;

        window.open(whatsappLink, '_blank');
    });
});
