'use client';

import { useState, useEffect } from 'react';
import { History, X, Pill, FileText, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api, SOAPResponse } from '@/lib/api';
import { getGlassStyles, getTextStyles } from '../styles';
import { ModalHistoricoConsultaProps } from '../types';

export function ModalHistoricoConsulta({ isOpen, onClose, consulta, pacienteNome }: ModalHistoricoConsultaProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();
  const [detalhes, setDetalhes] = useState<{
    soap?: SOAPResponse;
    receitas?: any[];
    exames?: any[];
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && consulta) {
      carregarDetalhes();
    }
  }, [isOpen, consulta]);

  const carregarDetalhes = async () => {
    if (!consulta) return;

    try {
      setLoading(true);
      // Carregar SOAP da consulta
      const soap = await api.getSOAP(consulta.id).catch(() => null);
      // Carregar receitas
      const receitas = await api.getReceitas(consulta.id).catch(() => []);

      setDetalhes({ soap: soap || undefined, receitas: receitas || [] });
    } catch (error) {
      console.error('Erro ao carregar detalhes:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className={cn('relative w-full max-w-4xl max-h-[85vh] overflow-hidden', glass.glassStrong, 'rounded-2xl')}>
        {/* Header */}
        <div className={cn('flex items-center justify-between p-4 border-b border-white/10')}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <History className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className={cn('text-lg font-bold', text.primary)}>
                Consulta de {consulta ? new Date(consulta.data).toLocaleDateString('pt-BR') : ''}
              </h2>
              <p className={cn('text-sm', text.muted)}>
                {pacienteNome} {consulta?.medico_nome && `• Dr(a). ${consulta.medico_nome}`}
              </p>
            </div>
          </div>
          <button onClick={onClose} className={cn('p-2 rounded-lg hover:bg-white/10', text.muted)}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[calc(85vh-80px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className={cn('w-8 h-8 animate-spin', text.muted)} />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Motivo */}
              {consulta?.motivo && (
                <div className={cn('p-4 rounded-xl', glass.glassSubtle)}>
                  <h3 className={cn('font-medium mb-2', text.primary)}>Motivo da Consulta</h3>
                  <p className={cn('text-sm', text.secondary)}>{consulta.motivo}</p>
                </div>
              )}

              {/* SOAP */}
              {detalhes?.soap && (
                <div className={cn('p-4 rounded-xl', glass.glassSubtle)}>
                  <h3 className={cn('font-medium mb-3', text.primary)}>Prontuário SOAP</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {detalhes.soap.subjetivo && (
                      <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-blue-400 font-medium">[S] Subjetivo</span>
                        </div>
                        <p className={cn('text-sm whitespace-pre-wrap', text.secondary)}>{detalhes.soap.subjetivo}</p>
                      </div>
                    )}
                    {detalhes.soap.objetivo && (
                      <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-green-400 font-medium">[O] Objetivo</span>
                        </div>
                        <p className={cn('text-sm whitespace-pre-wrap', text.secondary)}>{detalhes.soap.objetivo}</p>
                      </div>
                    )}
                    {detalhes.soap.avaliacao && (
                      <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-purple-400 font-medium">[A] Avaliação</span>
                        </div>
                        <p className={cn('text-sm whitespace-pre-wrap', text.secondary)}>{detalhes.soap.avaliacao}</p>
                      </div>
                    )}
                    {detalhes.soap.plano && (
                      <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-amber-400 font-medium">[P] Plano</span>
                        </div>
                        <p className={cn('text-sm whitespace-pre-wrap', text.secondary)}>{detalhes.soap.plano}</p>
                      </div>
                    )}
                  </div>

                  {/* Sinais Vitais */}
                  {detalhes.soap.exame_fisico && (
                    <div className="mt-4">
                      <h4 className={cn('font-medium mb-2', text.primary)}>Sinais Vitais</h4>
                      <div className="flex flex-wrap gap-3">
                        {detalhes.soap.exame_fisico.pa_sistolica && detalhes.soap.exame_fisico.pa_diastolica && (
                          <div className={cn('px-3 py-2 rounded-lg', glass.glassDark)}>
                            <span className={text.muted}>PA:</span>{' '}
                            <span className={text.primary}>{detalhes.soap.exame_fisico.pa_sistolica}/{detalhes.soap.exame_fisico.pa_diastolica} mmHg</span>
                          </div>
                        )}
                        {detalhes.soap.exame_fisico.fc && (
                          <div className={cn('px-3 py-2 rounded-lg', glass.glassDark)}>
                            <span className={text.muted}>FC:</span>{' '}
                            <span className={text.primary}>{detalhes.soap.exame_fisico.fc} bpm</span>
                          </div>
                        )}
                        {detalhes.soap.exame_fisico.peso && (
                          <div className={cn('px-3 py-2 rounded-lg', glass.glassDark)}>
                            <span className={text.muted}>Peso:</span>{' '}
                            <span className={text.primary}>{detalhes.soap.exame_fisico.peso} kg</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* CIDs */}
                  {detalhes.soap.cids && detalhes.soap.cids.length > 0 && (
                    <div className="mt-4">
                      <h4 className={cn('font-medium mb-2', text.primary)}>Diagnósticos (CID-10)</h4>
                      <div className="flex flex-wrap gap-2">
                        {detalhes.soap.cids.map((cid, i) => (
                          <span key={i} className={cn('px-2 py-1 rounded text-sm',
                            cid.tipo === 'principal' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-500/20 text-gray-400'
                          )}>
                            {cid.codigo} - {cid.descricao}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Receitas */}
              {detalhes?.receitas && detalhes.receitas.length > 0 && (
                <div className={cn('p-4 rounded-xl', glass.glassSubtle)}>
                  <h3 className={cn('font-medium mb-3', text.primary)}>Receitas</h3>
                  {detalhes.receitas.map((receita: any, i: number) => (
                    <div key={i} className={cn('p-3 rounded-lg mb-2', glass.glassDark)}>
                      <div className="flex items-center gap-2 mb-2">
                        <Pill className="w-4 h-4 text-green-400" />
                        <span className={cn('font-medium', text.primary)}>Receita {receita.tipo}</span>
                      </div>
                      <div className="space-y-1">
                        {receita.itens?.map((item: any, j: number) => (
                          <p key={j} className={cn('text-sm', text.secondary)}>
                            • {item.medicamento} {item.concentracao} - {item.posologia}
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Sem dados */}
              {!detalhes?.soap && (!detalhes?.receitas || detalhes.receitas.length === 0) && (
                <div className={cn('p-8 text-center', glass.glassSubtle, 'rounded-xl')}>
                  <FileText className={cn('w-12 h-12 mx-auto mb-3', text.muted)} />
                  <p className={text.muted}>Nenhum registro detalhado para esta consulta</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
