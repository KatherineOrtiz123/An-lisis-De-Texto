async function analizarSentimientos() {
    const inputText = document.getElementById('inputText').value;
    const resultado = document.getElementById('resultado');

    if (inputText.trim() === "") {
        resultado.textContent = "Por favor, ingresa un texto.";
        return;
    }

    try {
        const response = await fetch(`/sentimientos/${encodeURIComponent(inputText)}`);
        const data = await response.json();
        resultado.textContent = `Calificacion: ${data}`;
    } catch (error) {
        console.error('Error:', error);
        resultado.textContent = "Ocurrió un error al analizar los sentimientos.";
    }
}
