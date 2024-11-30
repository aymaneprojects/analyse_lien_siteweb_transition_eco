let currentStep = 0;
const titles = JSON.parse('{{ titles|tojson }}'.replace(/&quot;/g, '"'));
const totalSteps = titles.length + 3; // +3 pour les étapes supplémentaires après le scraping

function updateStatus() {
    if (currentStep < titles.length) {
        const progress = ((currentStep + 1) / totalSteps) * 100;
        document.getElementById("status-text").innerText = `Scraping : ${titles[currentStep]}`;
        document.getElementById("progress-bar").style.width = progress + "%";
        currentStep++;
        setTimeout(updateStatus, 800); // Pause rapide entre les étapes
    } else if (currentStep === titles.length) {
        document.getElementById("status-text").innerText = "Scraping terminé. Fichier enregistré avec succès.";
        currentStep++;
        setTimeout(updateStatus, 1000);
    } else if (currentStep === titles.length + 1) {
        document.getElementById("status-text").innerText = "Attente de la réponse du LLM...";
        currentStep++;
        setTimeout(updateStatus, 1000);
    } else if (currentStep === titles.length + 2) {
        document.getElementById("status-text").innerText = "LLM : Analyse en cours...";
        currentStep++;
        setTimeout(updateStatus, 1000);
    } else {
        document.getElementById("status-text").innerText = "Le processus est terminé";
        setTimeout(() => {
            window.location.href = "{{ next_step_url }}";
        }, 2000);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    updateStatus();
});