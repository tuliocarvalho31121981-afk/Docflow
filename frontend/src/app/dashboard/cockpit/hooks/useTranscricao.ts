'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { TRANSCRICAO_SIMULADA } from '../mocks';

interface UseTranscricaoOptions {
  useMockData?: boolean;
  consultaId?: string;
  onTranscricaoUpdate?: (transcricao: string) => void;
  onError?: (erro: string) => void;
}

export function useTranscricao(options: UseTranscricaoOptions = {}) {
  const { useMockData = true, consultaId, onTranscricaoUpdate, onError } = options;

  const [transcricao, setTranscricao] = useState<string>('');
  const [gravando, setGravando] = useState(false);
  const [processando, setProcessando] = useState(false);
  const [tempoGravacao, setTempoGravacao] = useState(0);
  const [erro, setErro] = useState<string | null>(null);

  // Referências para gravação real
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // Limpar transcrição
  const limparTranscricao = useCallback(() => {
    setTranscricao('');
    setTempoGravacao(0);
    setErro(null);
  }, []);

  // Função para enviar áudio para API
  const enviarAudioParaAPI = useCallback(async (audioBlob: Blob) => {
    if (!consultaId) {
      console.warn('[Transcrição] consultaId não definido, usando modo offline');
      setTranscricao(prev => prev + '\n\n[Áudio gravado - ' + (audioBlob.size / 1024).toFixed(1) + 'KB - aguardando consultaId para transcrever]');
      return;
    }

    try {
      setProcessando(true);
      setErro(null);

      console.log('[Transcrição] Enviando áudio para API...', {
        consultaId,
        audioSize: audioBlob.size,
        audioType: audioBlob.type,
      });

      const response = await api.transcreverAudio(consultaId, audioBlob);

      console.log('[Transcrição] Resposta recebida:', response);

      if (response.texto) {
        setTranscricao(prev => {
          const novaTranscricao = prev ? prev + '\n\n' + response.texto : response.texto;
          return novaTranscricao;
        });
      }
    } catch (error) {
      console.error('[Transcrição] Erro ao transcrever:', error);
      const mensagemErro = error instanceof Error ? error.message : 'Erro desconhecido na transcrição';
      setErro(mensagemErro);
      onError?.(mensagemErro);
    } finally {
      setProcessando(false);
    }
  }, [consultaId, onError]);

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
          const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              sampleRate: 16000,
            }
          });

          streamRef.current = stream;

          // Verificar codecs suportados
          const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
            ? 'audio/webm;codecs=opus'
            : MediaRecorder.isTypeSupported('audio/webm')
              ? 'audio/webm'
              : 'audio/mp4';

          console.log('[Transcrição] Usando codec:', mimeType);

          const mediaRecorder = new MediaRecorder(stream, { mimeType });
          mediaRecorderRef.current = mediaRecorder;
          audioChunksRef.current = [];

          mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              audioChunksRef.current.push(event.data);
              console.log('[Transcrição] Chunk recebido:', event.data.size, 'bytes');
            }
          };

          mediaRecorder.onstop = async () => {
            console.log('[Transcrição] Gravação parada, processando...');

            const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
            console.log('[Transcrição] Áudio total:', audioBlob.size, 'bytes');

            // Parar todas as tracks do stream
            streamRef.current?.getTracks().forEach(track => track.stop());
            streamRef.current = null;

            // Enviar para API
            await enviarAudioParaAPI(audioBlob);
          };

          mediaRecorder.onerror = (event) => {
            console.error('[Transcrição] Erro no MediaRecorder:', event);
            setErro('Erro durante a gravação');
            setGravando(false);
          };

          // Iniciar gravação com chunks de 1 segundo
          mediaRecorder.start(1000);
          console.log('[Transcrição] Gravação iniciada');

        } catch (error) {
          console.error('[Transcrição] Erro ao acessar microfone:', error);

          let mensagemErro = 'Não foi possível acessar o microfone.';
          if (error instanceof DOMException) {
            if (error.name === 'NotAllowedError') {
              mensagemErro = 'Permissão de microfone negada. Verifique as configurações do navegador.';
            } else if (error.name === 'NotFoundError') {
              mensagemErro = 'Nenhum microfone encontrado.';
            }
          }

          setErro(mensagemErro);
          onError?.(mensagemErro);
          setGravando(false);
        }
      }
    }
  }, [gravando, useMockData, enviarAudioParaAPI, onError]);

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

  // Cleanup ao desmontar
  useEffect(() => {
    return () => {
      // Parar gravação se estiver ativa
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      // Liberar stream
      streamRef.current?.getTracks().forEach(track => track.stop());
    };
  }, []);

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
    processando,
    tempoGravacao,
    erro,
    toggleGravacao,
    limparTranscricao,
    formatTempo,
  };
}
