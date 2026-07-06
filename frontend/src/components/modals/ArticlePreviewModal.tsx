import { createPortal } from 'react-dom';
import { X, Lock, MessageCircle, Share2, Volume2 } from 'lucide-react';
import type { Story } from '../../types';

interface ArticlePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  story: Story;
}

const EL_PAIS_FONTS = `
  @font-face {
    font-family: 'MajritTx';
    font-weight: 900;
    font-style: normal;
    font-display: swap;
    src: url('https://static.elpais.com/dist/resources/fonts/majrit/majrit-text/Majrit-Text-Black.woff2') format('woff2');
  }
  @font-face {
    font-family: 'MajritTx';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('https://static.elpais.com/dist/resources/fonts/majrit/majrit-text/Majrit-Text-Bold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'MajritTxRoman';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('https://static.elpais.com/dist/resources/fonts/majrit/majrit-text/Majrit-Text-Roman.woff2') format('woff2');
  }
`;

function formatDateline(dateStr: string): string {
  const d = new Date(dateStr);
  const months = [
    'ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC',
  ];
  const day = d.getDate();
  const month = months[d.getMonth()];
  const year = d.getFullYear();
  const time = d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  return `${day} ${month} ${year} - ${time} CEST`;
}

export function ArticlePreviewModal({ isOpen, onClose, story }: ArticlePreviewModalProps) {
  if (!isOpen) return null;

  const bodyText = story.description || '';

  return createPortal(
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 p-4 animate-fade-in" onClick={onClose}>
      <style>{EL_PAIS_FONTS}</style>
      <div
        className="relative w-full max-w-3xl max-h-[90vh] overflow-hidden rounded-lg shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Fake browser chrome */}
        <div className="flex items-center gap-2 px-4 h-10 bg-[#e9e9e9] flex-shrink-0">
          <div className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
          </div>
          <div className="flex-1 mx-3 h-6 rounded bg-white flex items-center px-3 gap-1.5 text-[11px] text-[#555]">
            <Lock className="w-3 h-3 text-[#555]" />
            elpais.com/articulo/{story.id}.html
          </div>
          <button onClick={onClose} className="text-[#555] hover:text-black">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Article page mock */}
        <div
          className="overflow-y-auto flex-1 bg-white"
          style={{ fontFamily: 'MajritTxRoman, Georgia, serif', color: '#111' }}
        >
          {/* El País header bar */}
          <div className="flex items-center justify-between px-6 h-14 border-b border-black/10">
            <img src="/el-pais-logo.svg" alt="El País" className="h-6 w-auto" />
            <button
              className="text-[11px] font-bold uppercase tracking-wide px-3 py-1.5 rounded-sm text-white"
              style={{ backgroundColor: '#016ca2', fontFamily: 'MarcinAntB, sans-serif' }}
            >
              Suscríbete
            </button>
          </div>

          <div className="max-w-2xl mx-auto px-6 py-8">
            {/* Category */}
            <div className="mb-3">
              <span
                className="inline-block text-[13px] font-bold uppercase tracking-wide pb-1 border-b-[3px] border-black"
                style={{ fontFamily: 'MarcinAntB, sans-serif' }}
              >
                Redacción con IA
              </span>
            </div>

            {/* Headline */}
            <h1
              className="text-[2rem] leading-[1.1] font-black tracking-tight mb-4"
              style={{ fontFamily: 'MajritTx, Georgia, serif', letterSpacing: '-0.02em' }}
            >
              {story.title}
            </h1>

            {/* Byline */}
            <div className="flex items-center gap-2 text-[13px] text-[#555] mb-5" style={{ fontFamily: 'MarcinAntB, sans-serif' }}>
              <span className="font-bold text-black">Redacción EL PAÍS</span>
              <span>Madrid - {formatDateline(story.updated_at || story.created_at)}</span>
            </div>

            {/* Audio + share row */}
            <div className="flex items-center gap-4 py-3 border-y border-black/10 mb-6 text-[#016ca2]">
              <button className="flex items-center gap-1.5 text-[13px] font-medium">
                <Volume2 className="w-4 h-4" />
                Escuchar
              </button>
              <button className="flex items-center gap-1.5 text-[13px] font-medium">
                <Share2 className="w-4 h-4" />
                Compartir
              </button>
              <button className="flex items-center gap-1.5 text-[13px] font-medium ml-auto">
                <MessageCircle className="w-4 h-4" />
                Ir a los comentarios
              </button>
            </div>

            {/* Hero image placeholder */}
            <div className="w-full aspect-[16/9] bg-gradient-to-br from-gray-200 to-gray-300 rounded-sm mb-2 flex items-center justify-center">
              <img src="/el-pais-logo.svg" alt="" className="h-8 w-auto opacity-30" />
            </div>
            <p className="text-[11px] text-[#777] mb-6">
              Ilustración generada para la demo. / EL PAÍS
            </p>

            {/* Body */}
            <div
              className="text-[19px] leading-[1.6] space-y-4"
              style={{ fontFamily: 'MajritTxRoman, Georgia, serif' }}
            >
              {(bodyText || 'Sin contenido de artículo todavía.')
                .split('\n')
                .filter(Boolean)
                .map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
            </div>
          </div>

          <div className="border-t border-black/10 px-6 py-4 text-center text-[11px] text-[#999]">
            © Ediciones EL PAÍS, S.L. — Vista previa generada para demostración
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
