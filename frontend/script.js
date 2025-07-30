document.addEventListener('DOMContentLoaded', () => {
    const nicknameInput = document.getElementById('nickname-input');
    const recommendBtn = document.getElementById('recommend-btn');
    const resultsContainer = document.getElementById('results-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorMessage = document.getElementById('error-message');

    // Função principal
    async function getRecommendations() {
        const nickname = nicknameInput.value.trim();
        errorMessage.textContent = '';
        resultsContainer.innerHTML = '';

        if (!nickname) {
            errorMessage.textContent = 'Por favor, insira um nickname do Letterboxd.';
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(`http://localhost:5000/recommend?nickname=${encodeURIComponent(nickname)}`);

            if (!response.ok) {
                const data = await response.json();
                errorMessage.textContent = data.error || 'Erro ao buscar recomendações.';
                return;
            }

            const recommendations = await response.json();

            if (recommendations.length === 0) {
                resultsContainer.innerHTML = '<p>Nenhuma recomendação encontrada.</p>';
                return;
            }

            // Renderizar recomendações
            recommendations.forEach(movie => {
                const movieCard = document.createElement('div');
                movieCard.classList.add('movie-card');

                movieCard.innerHTML = `
                    <h3>${movie.title} (${movie.year})</h3>
                    <p><strong>Gênero:</strong> ${movie.genre}</p>
                    <p><strong>Diretor:</strong> ${movie.director}</p>
                    <p><strong>Estrela:</strong> ${movie.star}</p>
                    <p><strong>Idioma:</strong> ${movie.language}</p>
                    <p><strong>Nota IMDb:</strong> ${movie.rating_imdb}</p>
                `;

                resultsContainer.appendChild(movieCard);
            });

        } catch (error) {
            console.error('Erro na requisição:', error);
            errorMessage.textContent = 'Erro ao conectar com o servidor. Verifique se o backend está rodando.';
        } finally {
            setLoading(false);
        }
    }

    // Controla o estado de carregamento
    function setLoading(isLoading) {
        if (isLoading) {
            loadingSpinner.classList.remove('hidden');
            recommendBtn.disabled = true;
        } else {
            loadingSpinner.classList.add('hidden');
            recommendBtn.disabled = false;
        }
    }

    // Clique no botão
    recommendBtn.addEventListener('click', getRecommendations);

    // Pressionar Enter ativa o botão
    nicknameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            getRecommendations();
        }
    });
});
