const { chromium } = require('playwright');
const fs = require('fs');
const https = require('https'); // Module natif ultra-stable pour remplacer fetch

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
  
  console.log(`[Étape 1] Connexion à la page de recherche...`);
  await page.goto(SEARCH_URL, { waitUntil: 'networkidle' });

  const bookLinks = await page.evaluate((base) => {
    const links = [];
    document.querySelectorAll('a[href*="/book/"]').forEach(a => {
      let href = a.getAttribute('href');
      if (href) {
        const fullUrl = href.startsWith('http') ? href : base + href;
        if (!links.includes(fullUrl)) links.push(fullUrl);
      }
    });
    return links;
  }, BASE_URL);

  console.log(`-> Nombre de liens de livres trouvés : ${bookLinks.length}`);

  let seenBooks = [];
  if (fs.existsSync(DB_FILE)) {
    seenBooks = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
  }

  const newBookLinks = bookLinks.filter(link => !seenBooks.includes(link));
  console.log(`-> ${newBookLinks.length} nouveau(x) livre(s) à traiter.`);

  // BRIDAGE DU PREMIER RUN : Sécurité fixée à 10 livres maximum
  const limitedLinks = newBookLinks.slice(0, 10);
  if (newBookLinks.length > 0) {
    console.log(`[Sécurité] Traitement limité aux ${limitedLinks.length} premiers livres.`);
  }

  // [Étape 2] Boucle sur chaque fiche de livre
  for (const link of limitedLinks) {
    try {
      console.log(`Visite de la fiche : ${link}`);
      await page.goto(link, { waitUntil: 'networkidle' });

      const bookDetails = await page.evaluate((base, currentLink) => {
        const titleEl = document.querySelector('a.title');
        const authorEl = document.querySelector('.author a');
        const coverEl = document.querySelector('img.cover');
        const descEl = document.querySelector('#bookDescriptionBox p');
        const dlEl = document.querySelector('a.addDownloadedBook');

        let cleanTitle = '';
        if (titleEl && titleEl.textContent && titleEl.textContent.trim().length > 0) {
          cleanTitle = titleEl.textContent.trim();
        } else {
          cleanTitle = currentLink.split('/').pop().replace('.html', '').replace(/-/g, ' ');
          cleanTitle = cleanTitle.replace(/\b\w/g, l => l.toUpperCase());
        }

        let dlHref = dlEl?.getAttribute('href') || '';
        const dlLink = dlHref.startsWith('http') ? dlHref : base + dlHref;

        return {
          title: cleanTitle || 'Sans titre',
          author: authorEl?.textContent?.trim() || 'Auteur inconnu',
          coverUrl: coverEl?.getAttribute('src') || '',
          description: descEl?.textContent?.trim() || 'Pas de résumé disponible.',
          downloadUrl: dlLink
        };
      }, BASE_URL, link);

      console.log(`   [OK] Extraction réussie pour : "${bookDetails.title}"`);

      if (bookDetails.description.length > 650) {
        bookDetails.description = bookDetails.description.substring(0, 650) + '...';
      }

      // Envoi vers Discord via la nouvelle méthode robuste
      await sendToDiscord(bookDetails, link);
      
      seenBooks.push(link);
      await new Promise(r => setTimeout(r, 3000));

    } catch (err) {
      console.error(`   [ERREUR] Impossible de récupérer les infos de la fiche ${link}:`, err);
    }
  }

  fs.writeFileSync(DB_FILE, JSON.stringify(seenBooks, null, 2));
  await browser.close();
  console.log("[Fin] Toutes les nouveautés du jour ont été vérifiées.");
})();

// Nouvelle fonction d'envoi utilisant le module HTTPS natif (évite le bug du exit code 1)
function sendToDiscord(details, bookUrl) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
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
        footer: { text: "Club de Lecture - Modération" },
        timestamp: new Date().toISOString()
      }]
    });

    const urlObj = new URL(DISCORD_WEBHOOK_URL);
    const options = {
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    };

    const req = https.request(options, (res) => {
      if (res.statusCode >= 200 && res.statusCode < 300) {
        resolve();
      } else {
        reject(new Error(`Discord a répondu avec le code : ${res.statusCode}`));
      }
    });

    req.on('error', (e) => {
      reject(e);
    });

    req.write(payload);
    req.end();
  });
}
