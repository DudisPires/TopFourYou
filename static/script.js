document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("nickname-input");
    const button = document.getElementById("recommend-btn");
    const results = document.getElementById("results-container");
    const errorMessage = document.getElementById("error-message");
    const spinner = document.getElementById("loading-spinner");

    button.addEventListener("click", async () => {
        const nickname = input.value.trim();
        if (!nickname) {
            errorMessage.textContent = "Por favor, digite um nickname.";
            return;
        }

        errorMessage.textContent = "";
        results.innerHTML = "";
        spinner.classList.remove("hidden");

        try {
            const response = await fetch(`/recommend?nickname=${nickname}`);
            const data = await response.json();

            spinner.classList.add("hidden");

            if (response.ok) {
                results.innerHTML = data.map(item => {
                    return `
                        <div class="recommendation-item">
                            <strong class="item-title">${item.title}</strong><br>
                            <span class="item-detail"><strong>Tipo:</strong> ${item.type}</span><br>
                            <span class="item-detail"><strong>Gênero:</strong> ${item.genre}</span><br>
                            <span class="item-detail"><strong>Data de Lançamento:</strong> ${item.release_date}</span><br>
                            <span class="item-detail"><strong>Diretor:</strong> ${item.director}</span>
                            <hr>
                        </div>
                    `;
                }).join("");
            }

            else {
                errorMessage.textContent = data.error || "Erro ao buscar recomendações.";
            }
        } catch (err) {
            spinner.classList.add("hidden");
            errorMessage.textContent = "Erro de conexão com o servidor.";
        }
    });
});
