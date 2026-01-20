'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { TRANSCRICAO_SIMULADA } from '../mocks';

interface UseTranscricaoOptions {
  useMockData?: boolean;
  onTranscricaoUpdate?: (transcricao: string) => void;
}

export function useTranscricao(options: UseTranscricaoOptions = {}) {
  const { useMockData = true, onTranscricaoUpdate } = options;

  const [transcricao, setTranscricao] = useState<string>('');
  const [gravando, setGravando] = useState(false);
  const [tempoGravacao, setTempoGravacao] = useState(0);
  const [erro, setErro] = useState<string | null>(null);

  // Referências para gravação real
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Limpar transcrição
  const limparTranscricao = useCallback(() => {
    setTranscricao('');
    setTempoGravacao(0);
  }, []);

  // Toggle gravação
  const toggleGravacao = useCallback(async () => {
    if (gravando) {
      // Parar gravação
      setGravando(false);

      if (!useMockData && mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
    } else {
      // Iniciar gravação
      setGravando(true);
      setTempoGravacao(0);
      setErro(null);

      if (useMockData) {
        // Modo demo: limpar transcrição anterior
        setTranscricao('');
      } else {
        // Modo real: iniciar captura de áudio
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          const mediaRecorder = new MediaRecorder(stream);
          mediaRecorderRef.current = mediaRecorder;
          audioChunksRef.current = [];

          mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              audioChunksRef.current.push(event.data);
            }
          };

          mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            console.log('Áudio gravado:', audioBlob.size, 'bytes');

            // TODO: Enviar para API de transcrição
            // const response = await api.transcreverAudio(audioBlob);
            // setTranscricao(response.texto);

            stream.getTracks().forEach(track => track.stop());
          };

          mediaRecorder.start(1000); // Capturar em chunks de 1 segundo
        } catch (error) {
          console.error('Erro ao acessar microfone:', error);
          setErro('Não foi possível acessar o microfone. Verifique as permissões.');
          setGravando(false);
        }
      }
    }
  }, [gravando, useMockData]);

  // Timer da gravação + simulação de transcrição em tempo real (modo demo)
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (gravando) {
      interval = setInterval(() => {
        setTempoGravacao(prev => {
          const novoTempo = prev + 1;

          // Modo demo: adicionar frase simulada a cada 5 segundos
          if (useMockData && novoTempo % 5 === 0) {
            const fraseIndex = Math.floor(novoTempo / 5) - 1;
            if (fraseIndex < TRANSCRICAO_SIMULADA.length) {
              const min = Math.floor(novoTempo / 60);
              const sec = novoTempo % 60;
              const timeStr = `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
              const frase = TRANSCRICAO_SIMULADA[fraseIndex].replace('{time}', timeStr);
              setTranscricao(prev => prev ? prev + '\n' + frase : frase);
            }
          }

          return novoTempo;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [gravando, useMockData]);

  // Notificar mudanças na transcrição
  useEffect(() => {
    if (onTranscricaoUpdate) {
      onTranscricaoUpdate(transcricao);
    }
  }, [transcricao, onTranscricaoUpdate]);

  // Formatar tempo de gravação
  const formatTempo = useCallback((segundos: number) => {
    const min = Math.floor(segundos / 60);
    const sec = segundos % 60;
    return `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
  }, []);

  return {
    transcricao,
    setTranscricao,
    gravando,
    tempoGravacao,
    erro,
    toggleGravacao,
    limparTranscricao,
    formatTempo,
  };
}
