document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("nickname-input");
    const button = document.getElementById("recommend-btn");
    const resultsContainer = document.getElementById("results-container");
    const avatarContainer = document.getElementById("avatar-container"); 
    const errorMessage = document.getElementById("error-message");
    const spinner = document.getElementById("loading-spinner");

    button.addEventListener("click", async () => {
        const nickname = input.value.trim();
        if (!nickname) {
            errorMessage.textContent = "Por favor, digite um nickname.";
            return;
        }

        errorMessage.textContent = "";
        resultsContainer.innerHTML = "";
        avatarContainer.innerHTML = ""; 
        spinner.classList.remove("hidden"); 

        try {
            const response = await fetch(`/recommend?nickname=${nickname}`);
            const data = await response.json();

            spinner.classList.add("hidden"); 

            if (response.ok) {
                if (data.avatar_url) {
                    const avatarImg = document.createElement("img");
                    avatarImg.src = data.avatar_url;
                    avatarImg.alt = `Avatar de ${nickname}`;
                    avatarImg.className = "avatar-img";
                    avatarContainer.appendChild(avatarImg); 
                }

                const filmes = data.recommendations;
                if (filmes && filmes.length > 0) {
                    resultsContainer.innerHTML = filmes.map(filme => `
                        <div class="filme">
                            <strong class="titulo">${filme.title}</strong><br>
                            <span class="genero">Gênero: ${filme.genre}</span><br>
                            <span class="idioma">Idioma: ${filme.language}</span><br>
                            <span class="nota">Nota IMDb: ${filme.rating_imdb}</span>
                            <hr>
                        </div>
                    `).join("");
                } else {
                    resultsContainer.innerHTML = "<p>Nenhuma recomendação encontrada.</p>";
                }
            } else {
                errorMessage.textContent = data.error || "Erro ao buscar recomendações.";
            }
        } catch (err) {
            spinner.classList.add("hidden");
            errorMessage.textContent = "Erro de conexão com o servidor.";
            console.error("Fetch error:", err);
        }
    });
});