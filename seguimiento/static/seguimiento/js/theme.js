// Manejador robusto de temas para Bootstrap 5
function aplicarAtributoTema(tema) {
    const html = document.documentElement;
    if (tema === 'dark') {
        html.setAttribute('data-bs-theme', 'dark');
    } else if (tema === 'light') {
        html.setAttribute('data-bs-theme', 'light');
    } else {
        // Modo Sistema
        const prefiereOscuro = window.matchMedia('(prefers-color-scheme: dark)').matches;
        html.setAttribute('data-bs-theme', prefiereOscuro ? 'dark' : 'light');
    }
}

function setTema(tema) {
    // 1. Guardar en memoria local del navegador
    localStorage.setItem('tesis_theme', tema.toLowerCase());
    
    // 2. Aplicar inmediatamente al elemento <html>
    aplicarAtributoTema(tema.toLowerCase());

    // 3. Opcional: Actualizar el icono o texto del botón si existe
    console.log("Tema cambiado a:", tema);
}

// Escuchar cambios del sistema en tiempo real si está en modo automático
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    const guardado = localStorage.getItem('tesis_theme') || 'system';
    if (guardado === 'system') {
        aplicarAtributoTema('system');
    }
});

function aplicarAtributoTema(tema) {
    const html = document.documentElement;
    const valor = (tema || '').toLowerCase();

    if (valor === 'dark') {
        html.setAttribute('data-bs-theme', 'dark');
    } else if (valor === 'light') {
        html.setAttribute('data-bs-theme', 'light');
    } else {
        const prefiereOscuro = window.matchMedia('(prefers-color-scheme: dark)').matches;
        html.setAttribute('data-bs-theme', prefiereOscuro ? 'dark' : 'light');
    }
}

function setTema(tema) {
    const valor = (tema || 'system').toLowerCase();
    localStorage.setItem('tesis_theme', valor);
    aplicarAtributoTema(valor);
}

// Escuchar cambios de preferencia del sistema operativo si se elige SYSTEM
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    const temaActual = localStorage.getItem('tesis_theme') || 'system';
    if (temaActual === 'system') {
        aplicarAtributoTema('system');
    }
});