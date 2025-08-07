// static/common.js

document.addEventListener("DOMContentLoaded", () => {
    const input1 = document.getElementById("nickname1-input");
    const input2 = document.getElementById("nickname2-input");
    const button = document.getElementById("find-common-btn");
    const results = document.getElementById("results-container");
    const errorMessage = document.getElementById("error-message");
    const spinner = document.getElementById("loading-spinner");

    button.addEventListener("click", async () => {
        const nickname1 = input1.value.trim();
        const nickname2 = input2.value.trim();

        if (!nickname1 || !nickname2) {
            errorMessage.textContent = "Por favor, digite os dois nicknames.";
            return;
        }

        errorMessage.textContent = "";
        results.innerHTML = "";
        spinner.classList.remove("hidden");

        try {
            const response = await fetch(`/find_common?nickname1=${nickname1}&nickname2=${nickname2}`);
            const data = await response.json();
            
            spinner.classList.add("hidden");

            if (response.ok) {
                if (data.length > 0) {
                    results.innerHTML = `<h3 class="results-title">Filmes em comum encontrados:</h3><ul>` + 
                        data.map(filme => `<li>${filme}</li>`).join("") + 
                        `</ul>`;
                } else {
                    results.innerHTML = `<p>Nenhum filme em comum foi encontrado nas watchlists.</p>`;
                }
            } else {
                errorMessage.textContent = data.error || "Erro ao buscar filmes em comum.";
            }
        } catch (err) {
            spinner.classList.add("hidden");
            errorMessage.textContent = "Erro de conexão com o servidor.";
            console.error(err);
        }
    });
});