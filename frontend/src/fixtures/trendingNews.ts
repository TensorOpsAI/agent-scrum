/**
 * Mocked "trending" news items for the demo. Sourced from real wire
 * headlines (labeled as trending for the demo, not pulled live). Each item
 * carries both the original English wire text and a pre-written Spanish
 * version in El País's editorial register, used when the item is added to
 * the board (simulates the "translate into our tone" agent step without
 * requiring a live LLM call).
 */

export interface TrendingNewsItem {
  id: string;
  source: string;
  category: string;
  originalTitle: string;
  originalTeaser: string;
  esTitle: string;
  esTeaser: string;
}

export const TRENDING_NEWS: TrendingNewsItem[] = [
  {
    id: 'trend-1',
    source: 'CNN',
    category: 'Mundial 2026',
    originalTitle:
      "'I didn't think it was a foul': Trump says he asked FIFA president for review of controversial red card",
    originalTeaser:
      'Trump confirmed he personally asked FIFA chief Gianni Infantino to review Balogun\'s red card, calling the incident a routine clash between players. Belgium has filed an appeal against the reversal.',
    esTitle:
      'Trump admite que pidió a la FIFA revisar la expulsión de Balogun: "No creí que fuera falta"',
    esTeaser:
      'El presidente estadounidense reconoce su intervención ante Gianni Infantino tras la controvertida decisión que permite al delantero jugar los octavos de final; Bélgica ya ha presentado un recurso.',
  },
  {
    id: 'trend-2',
    source: 'CNN',
    category: 'Internacional',
    originalTitle: "Trump's image stoned at funeral, state media footage shows",
    originalTeaser:
      "Mourners at Ayatollah Khamenei's funeral threw stones at an image of Donald Trump and displayed posters offering a bounty for his assassination, according to Iranian state media footage.",
    esTitle:
      'Imágenes de Irán muestran a asistentes al funeral de Jamenei apedreando un retrato de Trump',
    esTeaser:
      'Según la televisión estatal iraní, los asistentes lanzaron piedras contra una imagen del presidente estadounidense y exhibieron carteles con una recompensa por su muerte.',
  },
  {
    id: 'trend-3',
    source: 'CNN',
    category: 'Internacional',
    originalTitle:
      'Deadly Russian strikes hammer Kyiv on eve of Trump trip to critical NATO summit',
    originalTeaser:
      'At least 15 people were killed in Kyiv after a massive overnight barrage of Russian missiles and drones, hours before Trump was due to attend a NATO summit in Turkey focused on the war.',
    esTitle: 'Rusia lanza un ataque mortal contra Kiev en la víspera de la cumbre de la OTAN',
    esTeaser:
      'Al menos 15 personas murieron en la capital ucrania tras una oleada nocturna de misiles y drones rusos, horas antes de que Trump viaje a la cumbre de la OTAN en Turquía centrada en la guerra.',
  },
  {
    id: 'trend-4',
    source: 'CNN',
    category: 'Mundial 2026',
    originalTitle:
      'England sees off an immense challenge from Mexico in what may be the best game of the 2026 World Cup',
    originalTeaser:
      'England beat co-hosts Mexico 3-2 in a thrilling last-16 tie marked by a red card and four second-half goals, advancing to face Norway, who eliminated five-time champions Brazil.',
    esTitle:
      'Inglaterra sobrevive a México en un partido de infarto y clasifica para cuartos junto a Noruega',
    esTeaser:
      'Los ingleses se imponen 3-2 en el Estadio Azteca en un choque marcado por una expulsión y cuatro goles en la segunda parte; Noruega, verdugo de Brasil, será su próximo rival.',
  },
  {
    id: 'trend-5',
    source: 'CNN',
    category: 'Ciencia',
    originalTitle: 'This engineer literally lit up the world — and now wants to power it',
    originalTeaser:
      'Nobel laureate Shuji Nakamura, inventor of the blue LED, is now chasing a bigger breakthrough: a laser-based nuclear fusion power plant that could deliver limitless clean energy.',
    esTitle:
      'El ingeniero que iluminó el mundo con el LED azul ahora quiere darle energía ilimitada',
    esTeaser:
      'El premio Nobel Shuji Nakamura, inventor del LED azul, persigue un nuevo hito: una central de fusión nuclear por láser capaz de generar energía limpia e ilimitada antes de 2032.',
  },
];
