module.exports = {
  // Pliki HTML i szablony Django
  content: [
    './mapa/templates/**/*.html', // wszystkie szablony aplikacji
  ],
  // CSS do oczyszczenia
  css: [
    './mapa/static/css/*.css',  // wszystkie pliki CSS w katalogu css
  ],
  // Folder wyjściowy z oczyszczonym CSS
  output: './mapa/static/css/cleaned',
}
