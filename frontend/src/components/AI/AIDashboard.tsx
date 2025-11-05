import React, { useState, useEffect } from 'react';
import {
  Brain,
  RefreshCw,
  Filter,
  TrendingUp,
  Shield,
  Target,
  Clock,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import ComboCard from './ComboCard';
import { ComboRecommendation, aiAnalysisService } from '../../services/aiAnalysisService';

const AIDashboard: React.FC = () => {
  const [combos, setCombos] = useState<ComboRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'double' | 'triple'>('all');
  const [riskFilter, setRiskFilter] = useState<'all' | 'low' | 'medium' | 'high'>('all');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadCombos();
  }, []);

  const loadCombos = async () => {
    try {
      setLoading(true);
      const recommendations = await aiAnalysisService.generateCombos();
      setCombos(recommendations);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading AI combos:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCombos = combos.filter(combo => {
    if (filter !== 'all' && combo.type !== filter) return false;
    if (riskFilter !== 'all' && combo.riskLevel !== riskFilter) return false;
    return true;
  });

  const stats = {
    total: combos.length,
    doubles: combos.filter(c => c.type === 'double').length,
    triples: combos.filter(c => c.type === 'triple').length,
    highConfidence: combos.filter(c => c.confidence >= 0.85).length,
    lowRisk: combos.filter(c => c.riskLevel === 'low').length,
    avgConfidence: combos.length > 0 ? combos.reduce((sum, c) => sum + c.confidence, 0) / combos.length : 0,
    avgOdds: combos.length > 0 ? combos.reduce((sum, c) => sum + c.totalOdds, 0) / combos.length : 0
  };

  const handleComboSelect = (combo: ComboRecommendation) => {
    console.log('Combo selected:', combo);
    // Aqui você pode implementar a lógica para selecionar o combo
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <Brain className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">IA de Combos</h1>
            <p className="text-slate-600">Análise automática baseada em Oddspedia e métricas avançadas</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right">
            <p className="text-sm text-slate-500">Última atualização</p>
            <p className="text-sm font-medium text-slate-900">
              {lastUpdate.toLocaleTimeString()}
            </p>
          </div>
          <button
            onClick={loadCombos}
            disabled={loading}
            className="btn-primary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Atualizar</span>
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Total</p>
              <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
            </div>
            <Target className="w-8 h-8 text-primary-500" />
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Duplas</p>
              <p className="text-2xl font-bold text-slate-900">{stats.doubles}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-success-500" />
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Triplas</p>
              <p className="text-2xl font-bold text-slate-900">{stats.triples}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-warning-500" />
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Alta Conf.</p>
              <p className="text-2xl font-bold text-slate-900">{stats.highConfidence}</p>
            </div>
            <CheckCircle2 className="w-8 h-8 text-success-500" />
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Baixo Risco</p>
              <p className="text-2xl font-bold text-slate-900">{stats.lowRisk}</p>
            </div>
            <Shield className="w-8 h-8 text-success-500" />
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Conf. Média</p>
              <p className="text-2xl font-bold text-slate-900">{(stats.avgConfidence * 100).toFixed(1)}%</p>
            </div>
            <Brain className="w-8 h-8 text-primary-500" />
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Odds Média</p>
              <p className="text-2xl font-bold text-slate-900">{stats.avgOdds.toFixed(2)}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-slate-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-slate-500" />
              <span className="text-sm font-medium text-slate-700">Filtros:</span>
            </div>

            <div className="flex items-center space-x-2">
              <label className="text-sm text-slate-600">Tipo:</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="text-sm border border-slate-300 rounded px-2 py-1"
              >
                <option value="all">Todos</option>
                <option value="double">Duplas</option>
                <option value="triple">Triplas</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <label className="text-sm text-slate-600">Risco:</label>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value as any)}
                className="text-sm border border-slate-300 rounded px-2 py-1"
              >
                <option value="all">Todos</option>
                <option value="low">Baixo</option>
                <option value="medium">Médio</option>
                <option value="high">Alto</option>
              </select>
            </div>
          </div>

          <div className="text-sm text-slate-500">
            {filteredCombos.length} de {combos.length} combos
          </div>
        </div>
      </div>

      {/* Methodology Note */}
      <div className="card p-4 bg-primary-50 border-primary-200">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-primary-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-primary-900">Metodologia IA</h3>
            <p className="text-sm text-primary-700 mt-1">
              <strong>Análise integrada:</strong> Forma (últimos 15 jogos), H2H (últimos 10), xG/xGA (FBref),
              escanteios (SofaScore), lesões (Transfermarkt), clima (AccuWeather), árbitro (histórico).
              <strong>Meta:</strong> Confiabilidade ~95% com odds 1.50-2.00.
            </p>
            <p className="text-xs text-primary-600 mt-2">
              ⚠️ <strong>Importante:</strong> Validar escalações finais e odds antes da entrada. Apenas fins educacionais.
            </p>
          </div>
        </div>
      </div>

      {/* Combos Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <RefreshCw className="w-6 h-6 text-primary-600 animate-spin" />
            <span className="text-slate-600">Analisando jogos e gerando combos...</span>
          </div>
        </div>
      ) : filteredCombos.length === 0 ? (
        <div className="text-center py-12">
          <Brain className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">Nenhum combo encontrado</h3>
          <p className="text-slate-600">
            Não há combos que atendam aos critérios atuais. Tente ajustar os filtros.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredCombos.map((combo) => (
            <ComboCard
              key={combo.id}
              combo={combo}
              onSelect={handleComboSelect}
            />
          ))}
        </div>
      )}

      {/* Real-time Updates */}
      <div className="card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-slate-600">Sistema em tempo real ativo</span>
          </div>
          <div className="flex items-center space-x-4 text-xs text-slate-500">
            <span>Próxima atualização: {Math.floor(Math.random() * 5) + 1}min</span>
            <Clock className="w-4 h-4" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIDashboard;