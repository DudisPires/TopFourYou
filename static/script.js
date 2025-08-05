document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("nickname-input");
    const button = document.getElementById("recommend-btn");
    const results = document.getElementById("results-container");
    const errorMessage = document.getElementById("error-message");
    const spinner = document.getElementById("loading-spinner");
    spinner.classList.add("hidden");

    button.addEventListener("click", async () => {
        spinner.classList.add("hidden");
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
                results.innerHTML = data.map(filme => `
                    <div class="filme">
                        <strong class="titulo">${filme.title}</strong><br>
                        <span class="genero">Gênero: ${filme.genre}</span><br>
                        <span class="idioma">Idioma: ${filme.language}</span><br>
                        <span class="nota">Nota IMDb: ${filme.rating_imdb}</span>
                        <hr>
                    </div>
                `).join("");
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
