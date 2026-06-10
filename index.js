const { chromium } = require('playwright');
const fs = require('fs');

const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK;
const SEARCH_URL = 'https://z-lib.fm/s/?yearFrom=2026&languages%5B%5D=french&extensions%5B%5D=EPUB';
const DB_FILE = 'seen_books.json';
const BASE_URL = 'https://z-lib.fm';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();
  
  console.log("Analyse de la page de recherche...");
  await page.goto(SEARCH_URL, { waitUntil: 'networkidle' });

  // ÉTAPE A : Récupérer tous les liens des livres depuis la recherche
  const bookLinks = await page.evaluate((base) => {
    const links = [];
    document.querySelectorAll('a.title').forEach(a => {
      let href = a.getAttribute('href');
      if (href) {
        const fullUrl = href.startsWith('http') ? href : base + href;
        if (!links.includes(fullUrl)) links.push(fullUrl);
      }
    });
    return links;
  }, BASE_URL);

  let seenBooks = [];
  if (fs.existsSync(DB_FILE)) {
    seenBooks = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
  }

  const newBookLinks = bookLinks.filter(link => !seenBooks.includes(link));
  console.log(`${newBookLinks.length} nouveau(x) livre(s) trouvé(s).`);

  // ÉTAPE B : Boucler sur chaque nouveau livre pour extraire les détails
  for (const link of newBookLinks) {
    try {
      console.log(`Visite de la fiche : ${link}`);
      await page.goto(link, { waitUntil: 'networkidle' });

      const bookDetails = await page.evaluate((base) => {
        const titleEl = document.querySelector('.title');
        const authorEl = document.querySelector('.author a');
        const coverEl = document.querySelector('img.cover');
        const descEl = document.querySelector('#bookDescriptionBox p');
        const dlEl = document.querySelector('a.addDownloadedBook');

        let dlHref = dlEl?.getAttribute('href') || '';
        const dlLink = dlHref.startsWith('http') ? dlHref : base + dlHref;

        return {
          title: titleEl?.innerText?.trim() || 'Sans titre',
          author: authorEl?.innerText?.trim() || 'Auteur inconnu',
          coverUrl: coverEl?.getAttribute('src') || '',
          description: descEl?.innerText?.trim() || 'Pas de résumé disponible.',
          downloadUrl: dlLink
        };
      }, BASE_URL);

      if (bookDetails.description.length > 600) {
        bookDetails.description = bookDetails.description.substring(0, 600) + '...';
      }

      await sendToDiscord(link, bookDetails);
      seenBooks.push(link);
      await new Promise(r => setTimeout(r, 3000));

    } catch (err) {
      console.error(`Erreur sur le livre ${link}:`, err);
    }
  }

  fs.writeFileSync(DB_FILE, JSON.stringify(seenBooks, null, 2));
  await browser.close();
  console.log("Script exécuté avec succès !");
})();

async function sendToDiscord(bookUrl, details) {
  const payload = {
    embeds: [{
      title: `📚 ${details.title}`,
      url: bookUrl,
      color: 15105570,
      description: `**Résumé :**\n${details.description}`,
      fields: [
        { name: "✍️ Auteur", value: details.author, inline: true },
        { name: "📥 Téléchargement", value: `[Télécharger l'EPUB](${details.downloadUrl})`, inline: true }
      ],
      image: { url: details.coverUrl },
      footer: { text: "Alerte nouveauté Romantasy & Co" },
      timestamp: new Date().toISOString()
    }]
  };

  await fetch(DISCORD_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}
