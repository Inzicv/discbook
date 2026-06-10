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
  
  console.log(`[Étape 1] Connexion à la page de recherche...`);
  await page.goto(SEARCH_URL, { waitUntil: 'networkidle' });

  // Extraction de tous les liens de livres présents dans la liste de recherche
  const bookLinks = await page.evaluate((base) => {
    const links = [];
    // On attrape tous les liens qui mènent vers une fiche de livre
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

  // Gestion de l'historique pour ne pas doublonner
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

  // [Étape 2] Boucle sur chaque fiche de livre sélectionnée
  for (const link of limitedLinks) {
    try {
      console.log(`Visite de la fiche : ${link}`);
      await page.goto(link, { waitUntil: 'networkidle' });

      // Extraction des données en profondeur (Gestion des slots et du contenu brut HTML)
      const bookDetails = await page.evaluate((base, currentLink) => {
        const titleEl = document.querySelector('a.title');
        const authorEl = document.querySelector('.author a');
        const coverEl = document.querySelector('img.cover');
        const descEl = document.querySelector('#bookDescriptionBox p');
        const dlEl = document.querySelector('a.addDownloadedBook');

        // RUSE POUR LE TITRE : Si le slot masque le texte, on le nettoie depuis l'URL de la fiche
        let cleanTitle = '';
        if (titleEl && titleEl.textContent && titleEl.textContent.trim().length > 0) {
          cleanTitle = titleEl.textContent.trim();
        } else {
          // Fallback chirurgical via l'URL
          cleanTitle = currentLink.split('/').pop().replace('.html', '').replace(/-/g, ' ');
          cleanTitle = cleanTitle.replace(/\b\w/g, l => l.toUpperCase());
        }

        let dlHref = dlEl?.getAttribute('href') || '';
        const dlLink = dlHref.startsWith('http') ? dlHref : base + dlHref;

        return {
          title: cleanTitle || 'Sans titre',
          // .textContent force la lecture à travers le shadow DOM du composant
          author: authorEl?.textContent?.trim() || 'Auteur inconnu',
          coverUrl: coverEl?.getAttribute('src') || '',
          description: descEl?.textContent?.trim() || 'Pas de résumé disponible.',
          downloadUrl: dlLink
        };
      }, BASE_URL, link);

      console.log(`   [OK] Extraction réussie pour : "${bookDetails.title}"`);

      // Sécurité longueur de texte pour la mise en forme de Discord
      if (bookDetails.description.length > 650) {
        bookDetails.description = bookDetails.description.substring(0, 650) + '...';
      }

      // Envoi de la fiche finale vers le salon d'annonces de modération Discord
      await sendToDiscord(link, bookDetails);
      
      // Archivage immédiat du lien dans l'historique
      seenBooks.push(link);
      
      // Pause de 3 secondes pour ne pas surcharger le site cible
      await new Promise(r => setTimeout(r, 3000));

    } catch (err) {
      console.error(`   [ERREUR] Impossible de récupérer les infos de la fiche ${link}:`, err);
    }
  }

  // Sauvegarde définitive de l'historique mis à jour sur ton dépôt GitHub
  fs.writeFileSync(DB_FILE, JSON.stringify(seenBooks, null, 2));
  await browser.close();
  console.log("[Fin] Toutes les nouveautés du jour ont été vérifiées.");
})();

// Fonction de formatage pour envoyer la carte graphique sur Discord
async function sendToDiscord(bookUrl, details) {
  const payload = {
    embeds: [{
      title: `📚 ${details.title}`,
      url: bookUrl,
      color: 15105570, // Code couleur de la bordure latérale (Or/Orange)
      description: `**Résumé :**\n${details.description}`,
      fields: [
        { name: "✍️ Auteur", value: details.author, inline: true },
        { name: "📥 Téléchargement", value: `[Télécharger l'EPUB](${details.downloadUrl})`, inline: true }
      ],
      image: { url: details.coverUrl },
      footer: { text: "Club de Lecture - Modération" },
      timestamp: new Date().toISOString()
    }]
  };

  const response = await fetch(DISCORD_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Erreur API Discord: ${response.statusText}`);
  }
}
