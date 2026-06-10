const { chromium } = require('playwright');
const fs = require('fs');

const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK;
const SEARCH_URL = 'https://z-lib.fm/s/?yearFrom=2026&languages%5B%5D=french&extensions%5B%5D=EPUB';
const DB_FILE = 'seen_books.json';
const BASE_URL = 'https://z-lib.fm';

(async () => {
  console.log("Démarrage du script...");
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();
  
  await page.goto(SEARCH_URL, { waitUntil: 'networkidle' });

  // ÉTAPE A : On récupère les liens relatifs (ex: /book/k07maexpAJ/obsession-villain.html)
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
  console.log(`Nouveaux livres détectés : ${newBookLinks.length}`);

  // On garde les 10 derniers pour ton premier run de test
  const limitedLinks = newBookLinks.slice(0, 10);

  // ÉTAPE B : On visite chaque fiche
  for (const link of limitedLinks) {
    try {
      await page.goto(link, { waitUntil: 'networkidle' });

      const bookDetails = await page.evaluate((base, currentLink) => {
        const authorEl = document.querySelector('.author a');
        const coverEl = document.querySelector('img.cover, img.image');
        const descEl = document.querySelector('#bookDescriptionBox p');
        const dlEl = document.querySelector('a.addDownloadedBook');

        // ruse : si le titre HTML est vide à cause du <slot>, on extrait le nom depuis l'URL !
        // Exemple : /book/k07maexpAJ/obsession-villain.html -> "obsession-villain"
        let fallbackTitle = 'Livre sans titre';
        const parts = currentLink.split('/');
        const lastPart = parts[parts.length - 1]; // "obsession-villain.html"
        if (lastPart) {
          fallbackTitle = lastPart
            .replace('.html', '')
            .replace(/-/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase()); // Rend le titre propre : "Obsession Villain"
        }

        let dlHref = dlEl?.getAttribute('href') || '';
        const dlLink = dlHref ? (dlHref.startsWith('http') ? dlHref : base + dlHref) : '';

        return {
          title: fallbackTitle,
          author: authorEl?.innerText?.trim() || 'Auteur inconnu',
          coverUrl: coverEl?.getAttribute('src') || '',
          description: descEl?.innerText?.trim() || 'Pas de résumé disponible.',
          downloadUrl: dlLink
        };
      }, BASE_URL, link);

      if (bookDetails.description.length > 600) {
        bookDetails.description = bookDetails.description.substring(0, 600) + '...';
      }

      // Envoi à Discord
      await sendToDiscord(link, bookDetails);
      
      seenBooks.push(link);
      await new Promise(r => setTimeout(r, 2000));

    } catch (err) {
      console.error(`Erreur sur le lien ${link}:`, err);
    }
  }

  fs.writeFileSync(DB_FILE, JSON.stringify(seenBooks, null, 2));
  await browser.close();
  console.log("Exécution terminée !");
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
        { name: "📥 Téléchargement", value: details.downloadUrl ? `[Télécharger l'EPUB](${details.downloadUrl})` : "Non disponible", inline: true }
      ],
      image: details.coverUrl ? { url: details.coverUrl } : undefined,
      footer: { text: "Modération Club de Lecture" },
      timestamp: new Date().toISOString()
    }]
  };

  await fetch(DISCORD_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}
