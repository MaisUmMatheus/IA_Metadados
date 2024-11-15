document.getElementById('uploadForm').onsubmit = async (event) => {
    event.preventDefault();

    const formData = new FormData();
    formData.append('file', document.getElementById('fileInput').files[0]);

    try {
        // Faz a requisição POST para o endpoint /upload
        const response = await fetch('http://127.0.0.1:5000/upload', {
            method: 'POST',
            body: formData // Usa FormData diretamente no body
        });
adadadada
        if (response.ok) {
            alert("Arquivo enviado com sucesso!");
            // Fazer a requisição para classificar o arquivo
            await classificarArquivo(formData); // Chama a função para classificar o arquivo enviado
            fetchMetadados(); // Chama a função para atualizar os metadados
        } else if (response.status === 409) {
            alert("O arquivo já foi enviado anteriormente.");
        } else {
            const errorMessage = await response.json();
            alert("Erro ao enviar o arquivo: " + errorMessage.error);
        }
    } catch (error) {
        console.error("Erro ao enviar o arquivo:", error);
        alert("Erro ao enviar o arquivo.");
    }
};

// Função para classificar o arquivo usando a API do Gemini
async function classificarArquivo(formData) {
    try {
        // Faz a requisição POST para o endpoint /classificar
        const response = await fetch('http://127.0.0.1:5000/classificar', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            alert(`Categoria do arquivo: ${data.categoria}`);
        } else {
            alert("Erro ao classificar o arquivo.");
        }
    } catch (error) {
        console.error("Erro ao classificar o arquivo:", error);
        alert("Erro ao classificar o arquivo.");
    }
}

async function fetchMetadados() {
    try {
        const response = await fetch('http://127.0.0.1:5000/metadados');
        if (!response.ok) {
            throw new Error("Erro ao obter metadados.");
        }
        const metadados = await response.json();
        const metadadosContainer = document.getElementById('metadados');
        metadadosContainer.innerHTML = '';

        metadados.forEach(metadado => {
            const metadadoDiv = document.createElement('div');
            metadadoDiv.innerHTML = `
                <p><strong>Id:</strong> ${metadado[0]} | <strong>Data:</strong> ${metadado[1]} | 
                <strong>Nome do Arquivo:</strong> ${metadado[2]} | <strong>Formato:</strong> ${metadado[3]} | 
                <strong>Colunas:</strong> ${metadado[4]} | <strong>Categoria:</strong> ${metadado[5]}
                <button onclick="fetchDados(${metadado[0]})">Ver Dados</button>
                </p>
            `;
            metadadosContainer.appendChild(metadadoDiv);
        });
    } catch (error) {
        console.error("Erro ao buscar metadados:", error);
        alert("Erro ao buscar metadados.");
    }
}

async function fetchDados(metadado_id) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/dados/${metadado_id}`);
        if (!response.ok) {
            throw new Error("Erro ao obter dados do metadado.");
        }
        const dados = await response.json();
        const dadosContainer = document.getElementById('dados');
        dadosContainer.innerHTML = '';

        dados.forEach(dado => {
            const dadoDiv = document.createElement('div');
            dadoDiv.innerHTML = `
                <p><strong>Id do Metadado:</strong> ${dado[1]} | <strong>Nome da Coluna:</strong> ${dado[2]} | 
                <strong>Tipo de Dado:</strong> ${dado[3]} | <strong>Valor:</strong> ${dado[4]}</p>
            `;
            dadosContainer.appendChild(dadoDiv);
        });
    } catch (error) {
        console.error("Erro ao buscar dados:", error);
        alert("Erro ao buscar dados do metadado.");
    }
}

// Carrega os metadados ao abrir a página
fetchMetadados();
