/** Tailwind CSS 3.4.17. Кольори — з логотипу «Файна поляна» (див. 02-Стиль.md), шрифти — стиль 2015–2020. */
module.exports = {
  content: ['./*.html', './js/**/*.js'],
  theme: {
    extend: {
      colors: {
        berry: '#E4303C',      // малиновий логотипу — великі цифри, акценти
        berrydk: '#C42733',    // малиновий для кнопок і дрібного тексту (контраст ≥ 4.5:1)
        berrytx: '#B0222E',
        orange: '#F07830',
        orangetx: '#B4561A',
        leaf: '#78B454',
        leafdk: '#3F7A2A',     // зелений для тексту на білому (≥ 4.5:1)
        forest: '#26402A',
        forestdk: '#1D3220',
        graphite: '#2F3336',
        stone: '#545454',
        body: '#3A3F42',
        muted: '#5A5F63',
        rose: '#E4606C',
        pink: '#F09C9C',
        sprout: '#9CCC84',
        blush: '#FCE4E4',
        peach: '#FEF0E6',
        mint: '#EEF6E9',
        cloud: '#F6F6F4',
        line: '#E4E4E0',
        dangerText: '#A63828',
        successText: '#2A7048'
      },
      fontFamily: {
        sans: ['Roboto', 'system-ui', 'sans-serif'],
        slab: ['"Roboto Slab"', 'Georgia', 'serif'],
        script: ['"Marck Script"', 'cursive']
      }
    }
  }
};
