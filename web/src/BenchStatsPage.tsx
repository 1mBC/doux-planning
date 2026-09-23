import { useCallback, useEffect, useRef, useState } from "react";
import { effortLabel } from "./admin";
import { AdminNav } from "./AdminPage";
import { BENCH_EFFORTS, loadBenchVersions, type BenchVersionDataset, type BenchVersions } from "./bench";
import { ApiHttpError } from "./sandbox";
import type { SearchEffort } from "./generate";

type DataPoint = {
  ref: string;
  mean: number;
  min: number;
  max: number;
};

type PodiumCount = {
  ref: string;
  count: number;
};

const HOVER_THRESHOLD = 30;

const PODIUM_THRESHOLDS = [
  { key: "first", label: "1er", delta: 0 },
  { key: "at01", label: "À 0,1", delta: 0.1 },
  { key: "at02", label: "À 0,2", delta: 0.2 },
  { key: "at03", label: "À 0,3", delta: 0.3 },
] as const;

const PODIUM_COLORS: Record<string, { bar: string; light: string }> = {
  first: { bar: "#2563eb", light: "#3b82f6" },
  at01: { bar: "#059669", light: "#10b981" },
  at02: { bar: "#d97706", light: "#f59e0b" },
  at03: { bar: "#dc2626", light: "#ef4444" },
};

function computeStatsForEffort(datasets: BenchVersionDataset[], engineRefs: string[], effort: SearchEffort): DataPoint[] {
  const points: DataPoint[] = [];
  for (const ref of engineRefs) {
    const values: number[] = [];
    for (const dataset of datasets) {
      const cell = dataset.by_ref[ref]?.[effort];
      if (cell && cell.global !== null && Number.isFinite(cell.global)) {
        values.push(cell.global);
      }
    }
    if (values.length > 0) {
      points.push({
        ref,
        mean: values.reduce((a, b) => a + b, 0) / values.length,
        min: Math.min(...values),
        max: Math.max(...values),
      });
    }
  }
  return points;
}

function computePodiumCounts(
  datasets: BenchVersionDataset[],
  engineRefs: string[],
  effort: SearchEffort,
  delta: number,
): { counts: PodiumCount[]; totalDatasets: number } {
  const countMap = new Map<string, number>();
  for (const ref of engineRefs) {
    countMap.set(ref, 0);
  }

  let totalDatasets = 0;
  for (const dataset of datasets) {
    const globals: { ref: string; global: number }[] = [];
    for (const ref of engineRefs) {
      const cell = dataset.by_ref[ref]?.[effort];
      if (cell && cell.global !== null && Number.isFinite(cell.global)) {
        globals.push({ ref, global: cell.global });
      }
    }
    if (globals.length === 0) continue;

    totalDatasets++;
    const best = Math.max(...globals.map((g) => g.global));
    const threshold = best - delta;

    for (const ref of engineRefs) {
      const cell = dataset.by_ref[ref]?.[effort];
      if (cell && cell.global !== null && Number.isFinite(cell.global)) {
        if (delta === 0 ? cell.global === best : cell.global >= threshold) {
          countMap.set(ref, (countMap.get(ref) ?? 0) + 1);
        }
      }
    }
  }

  const counts: PodiumCount[] = engineRefs.map((ref) => ({
    ref,
    count: countMap.get(ref) ?? 0,
  }));

  return { counts, totalDatasets };
}

const GRAPH_WIDTH = 600;
const GRAPH_HEIGHT = 280;
const PADDING_LEFT = 48;
const PADDING_RIGHT = 24;
const PADDING_TOP = 24;
const PADDING_BOTTOM = 40;
const PLOT_WIDTH = GRAPH_WIDTH - PADDING_LEFT - PADDING_RIGHT;
const PLOT_HEIGHT = GRAPH_HEIGHT - PADDING_TOP - PADDING_BOTTOM;

function StatsGraph({ effort, points }: { effort: SearchEffort; points: DataPoint[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const allValues = points.flatMap((p) => [p.mean, p.min, p.max]);
  const minObserved = allValues.length > 0 ? Math.min(...allValues) : 0;
  const yMin = Math.max(0, minObserved - 0.4);
  const yMax = 10;
  const yRange = yMax - yMin;

  const xStep = points.length > 1 ? PLOT_WIDTH / (points.length - 1) : 0;

  const toX = useCallback(
    (index: number): number => {
      return PADDING_LEFT + (points.length > 1 ? index * xStep : PLOT_WIDTH / 2);
    },
    [points.length, xStep],
  );

  const toY = useCallback(
    (value: number): number => {
      return PADDING_TOP + PLOT_HEIGHT - ((value - yMin) / yRange) * PLOT_HEIGHT;
    },
    [yMin, yRange],
  );

  const handleMouseMove = useCallback(
    (event: React.MouseEvent<SVGSVGElement>) => {
      if (!svgRef.current || points.length === 0) {
        setHoverIndex(null);
        return;
      }
      const rect = svgRef.current.getBoundingClientRect();
      const scaleX = GRAPH_WIDTH / rect.width;
      const mouseX = (event.clientX - rect.left) * scaleX;

      let closestIndex = -1;
      let closestDist = Infinity;
      for (let i = 0; i < points.length; i++) {
        const px = toX(i);
        const dist = Math.abs(mouseX - px);
        if (dist < closestDist) {
          closestDist = dist;
          closestIndex = i;
        }
      }

      if (closestDist <= HOVER_THRESHOLD) {
        setHoverIndex(closestIndex);
      } else {
        setHoverIndex(null);
      }
    },
    [points, toX],
  );

  const handleMouseLeave = useCallback(() => {
    setHoverIndex(null);
  }, []);

  if (points.length === 0) {
    return null;
  }

  function buildPath(values: number[]): string {
    return values
      .map((v, i) => `${i === 0 ? "M" : "L"} ${toX(i).toFixed(1)} ${toY(v).toFixed(1)}`)
      .join(" ");
  }

  const meanPath = buildPath(points.map((p) => p.mean));
  const minPath = buildPath(points.map((p) => p.min));
  const maxPath = buildPath(points.map((p) => p.max));

  const yTicks: number[] = [];
  const tickStep = yRange <= 2 ? 0.5 : yRange <= 5 ? 1 : 2;
  for (let tick = Math.ceil(yMin / tickStep) * tickStep; tick <= yMax; tick += tickStep) {
    yTicks.push(tick);
  }

  const hoveredPoint = hoverIndex !== null ? points[hoverIndex] : null;
  const hoverX = hoverIndex !== null ? toX(hoverIndex) : 0;

  return (
    <article className="bench-stats-graph">
      <h3>{effortLabel(effort)}</h3>
      <div className="bench-stats-legend">
        <span className="bench-stats-legend-item bench-stats-legend-mean">Moyenne</span>
        <span className="bench-stats-legend-item bench-stats-legend-min">Min</span>
        <span className="bench-stats-legend-item bench-stats-legend-max">Max</span>
      </div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${GRAPH_WIDTH} ${GRAPH_HEIGHT}`}
        className="bench-stats-svg"
        aria-label={`Graphe ${effortLabel(effort)}`}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <line
          x1={PADDING_LEFT}
          y1={PADDING_TOP}
          x2={PADDING_LEFT}
          y2={PADDING_TOP + PLOT_HEIGHT}
          stroke="#888"
          strokeWidth="1"
        />
        <line
          x1={PADDING_LEFT}
          y1={PADDING_TOP + PLOT_HEIGHT}
          x2={PADDING_LEFT + PLOT_WIDTH}
          y2={PADDING_TOP + PLOT_HEIGHT}
          stroke="#888"
          strokeWidth="1"
        />

        {yTicks.map((tick) => (
          <g key={tick}>
            <line
              x1={PADDING_LEFT - 4}
              y1={toY(tick)}
              x2={PADDING_LEFT}
              y2={toY(tick)}
              stroke="#888"
              strokeWidth="1"
            />
            <text
              x={PADDING_LEFT - 8}
              y={toY(tick)}
              textAnchor="end"
              dominantBaseline="middle"
              className="bench-stats-tick"
            >
              {tick.toFixed(1).replace(".", ",")}
            </text>
          </g>
        ))}

        {points.map((point, i) => (
          <g key={point.ref}>
            <line
              x1={toX(i)}
              y1={PADDING_TOP + PLOT_HEIGHT}
              x2={toX(i)}
              y2={PADDING_TOP + PLOT_HEIGHT + 4}
              stroke="#888"
              strokeWidth="1"
            />
            <text
              x={toX(i)}
              y={PADDING_TOP + PLOT_HEIGHT + 12}
              textAnchor="middle"
              dominantBaseline="hanging"
              className="bench-stats-label"
            >
              {point.ref}
            </text>
          </g>
        ))}

        <path d={maxPath} fill="none" stroke="#2f6fed" strokeWidth="1.5" />
        <path d={minPath} fill="none" stroke="#c43a3a" strokeWidth="1.5" strokeDasharray="4 3" />
        <path d={meanPath} fill="none" stroke="#1c1917" strokeWidth="2.5" />

        {points.map((point, i) => (
          <g key={`dots-${point.ref}`}>
            <circle cx={toX(i)} cy={toY(point.max)} r="3" fill="#2f6fed" />
            <circle cx={toX(i)} cy={toY(point.min)} r="3" fill="#c43a3a" />
            <circle cx={toX(i)} cy={toY(point.mean)} r="4" fill="#1c1917" />
          </g>
        ))}

        {hoveredPoint !== null && (
          <g className="bench-stats-hover">
            <line
              x1={hoverX}
              y1={PADDING_TOP}
              x2={hoverX}
              y2={PADDING_TOP + PLOT_HEIGHT}
              stroke="#666"
              strokeWidth="1"
              strokeDasharray="4 4"
              opacity="0.7"
            />
            <g transform={`translate(${hoverX + 8}, ${toY(hoveredPoint.max) - 2})`}>
              <rect
                x="-2"
                y="-12"
                width="38"
                height="16"
                rx="4"
                fill="rgba(255,255,255,0.9)"
                stroke="#2f6fed"
                strokeWidth="0.5"
              />
              <text
                x="0"
                y="0"
                className="bench-stats-hover-label"
                fill="#2f6fed"
              >
                {hoveredPoint.max.toFixed(1)}
              </text>
            </g>
            <g transform={`translate(${hoverX}, ${toY(hoveredPoint.mean) - 16})`}>
              <rect
                x="-19"
                y="-12"
                width="38"
                height="16"
                rx="4"
                fill="rgba(255,255,255,0.9)"
                stroke="#1c1917"
                strokeWidth="0.5"
              />
              <text
                x="0"
                y="0"
                textAnchor="middle"
                className="bench-stats-hover-label"
                fill="#1c1917"
              >
                {hoveredPoint.mean.toFixed(1)}
              </text>
            </g>
            <g transform={`translate(${hoverX - 8}, ${toY(hoveredPoint.min) - 2})`}>
              <rect
                x="-36"
                y="-12"
                width="38"
                height="16"
                rx="4"
                fill="rgba(255,255,255,0.9)"
                stroke="#c43a3a"
                strokeWidth="0.5"
              />
              <text
                x="-17"
                y="0"
                textAnchor="middle"
                className="bench-stats-hover-label"
                fill="#c43a3a"
              >
                {hoveredPoint.min.toFixed(1)}
              </text>
            </g>
          </g>
        )}
      </svg>
    </article>
  );
}

const BAR_GRAPH_WIDTH = 400;
const BAR_GRAPH_HEIGHT = 200;
const BAR_PADDING_LEFT = 48;
const BAR_PADDING_RIGHT = 16;
const BAR_PADDING_TOP = 16;
const BAR_PADDING_BOTTOM = 48;
const BAR_PLOT_WIDTH = BAR_GRAPH_WIDTH - BAR_PADDING_LEFT - BAR_PADDING_RIGHT;
const BAR_PLOT_HEIGHT = BAR_GRAPH_HEIGHT - BAR_PADDING_TOP - BAR_PADDING_BOTTOM;

function PodiumBarChart({
  thresholdKey,
  label,
  counts,
  maxCount,
}: {
  thresholdKey: string;
  label: string;
  counts: PodiumCount[];
  maxCount: number;
}) {
  if (counts.length === 0 || maxCount === 0) {
    return null;
  }

  const barWidth = Math.min(40, BAR_PLOT_WIDTH / counts.length - 8);
  const gap = (BAR_PLOT_WIDTH - barWidth * counts.length) / (counts.length + 1);
  const colors = PODIUM_COLORS[thresholdKey] ?? PODIUM_COLORS.first;

  return (
    <article className="bench-podium-chart">
      <h4>{label}</h4>
      <svg
        viewBox={`0 0 ${BAR_GRAPH_WIDTH} ${BAR_GRAPH_HEIGHT}`}
        className="bench-podium-svg"
        aria-label={`Podium ${label}`}
      >
        <line
          x1={BAR_PADDING_LEFT}
          y1={BAR_PADDING_TOP}
          x2={BAR_PADDING_LEFT}
          y2={BAR_PADDING_TOP + BAR_PLOT_HEIGHT}
          stroke="#888"
          strokeWidth="1"
        />
        <line
          x1={BAR_PADDING_LEFT}
          y1={BAR_PADDING_TOP + BAR_PLOT_HEIGHT}
          x2={BAR_PADDING_LEFT + BAR_PLOT_WIDTH}
          y2={BAR_PADDING_TOP + BAR_PLOT_HEIGHT}
          stroke="#888"
          strokeWidth="1"
        />

        {[0, Math.ceil(maxCount / 2), maxCount].map((tick) => {
          const y = BAR_PADDING_TOP + BAR_PLOT_HEIGHT - (tick / maxCount) * BAR_PLOT_HEIGHT;
          return (
            <g key={tick}>
              <line x1={BAR_PADDING_LEFT - 4} y1={y} x2={BAR_PADDING_LEFT} y2={y} stroke="#888" strokeWidth="1" />
              <text x={BAR_PADDING_LEFT - 8} y={y} textAnchor="end" dominantBaseline="middle" className="bench-stats-tick">
                {tick}
              </text>
            </g>
          );
        })}

        {counts.map((item, i) => {
          const barHeight = maxCount > 0 ? (item.count / maxCount) * BAR_PLOT_HEIGHT : 0;
          const x = BAR_PADDING_LEFT + gap + i * (barWidth + gap);
          const y = BAR_PADDING_TOP + BAR_PLOT_HEIGHT - barHeight;

          return (
            <g key={item.ref}>
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                fill={item.count > 0 ? colors.bar : "#e5e7eb"}
                rx="2"
              />
              {item.count > 0 && (
                <text
                  x={x + barWidth / 2}
                  y={y - 4}
                  textAnchor="middle"
                  className="bench-podium-count"
                  fill={colors.bar}
                >
                  {item.count}
                </text>
              )}
              <text
                x={x + barWidth / 2}
                y={BAR_PADDING_TOP + BAR_PLOT_HEIGHT + 8}
                textAnchor="middle"
                dominantBaseline="hanging"
                className="bench-stats-label"
                transform={`rotate(45, ${x + barWidth / 2}, ${BAR_PADDING_TOP + BAR_PLOT_HEIGHT + 8})`}
              >
                {item.ref}
              </text>
            </g>
          );
        })}
      </svg>
    </article>
  );
}

function PodiumSection({
  effort,
  datasets,
  engineRefs,
}: {
  effort: SearchEffort;
  datasets: BenchVersionDataset[];
  engineRefs: string[];
}) {
  const podiumData = PODIUM_THRESHOLDS.map((t) => ({
    ...t,
    ...computePodiumCounts(datasets, engineRefs, effort, t.delta),
  }));

  const maxCount = podiumData.length > 0 ? podiumData[0].totalDatasets : 0;

  if (maxCount === 0) {
    return null;
  }

  return (
    <div className="bench-podium-section">
      <h3>{effortLabel(effort)} — Podiums</h3>
      <div className="bench-podium-grid">
        {podiumData.map((d) => (
          <PodiumBarChart key={d.key} thresholdKey={d.key} label={d.label} counts={d.counts} maxCount={maxCount} />
        ))}
      </div>
    </div>
  );
}

export function BenchStatsPage() {
  const [versions, setVersions] = useState<BenchVersions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    loadBenchVersions()
      .then((next) => {
        if (!cancelled.current) {
          setVersions(next);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled.current) {
          setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
        }
      });
    return () => {
      cancelled.current = true;
    };
  }, []);

  if (error) {
    return (
      <main className="page">
        <AdminNav current="bench-stats" />
        <p className="error" role="alert">
          {error}
        </p>
      </main>
    );
  }
  if (!versions) {
    return (
      <main className="page">
        <AdminNav current="bench-stats" />
        <p className="sub">Chargement des stats…</p>
      </main>
    );
  }

  const graphs = BENCH_EFFORTS.map((effort) => ({
    effort,
    points: computeStatsForEffort(versions.datasets, versions.engine_refs, effort),
  })).filter((g) => g.points.length > 0);

  return (
    <main className="page admin-page">
      <AdminNav current="bench-stats" />
      <h1>Stats banc</h1>
      <p className="sub">Notes globales par moteur · {versions.engine_ref || "—"}</p>

      {graphs.length === 0 ? (
        <p className="sub">Aucun run disponible.</p>
      ) : (
        <>
          <section className="bench-stats-graphs">
            {graphs.map(({ effort, points }) => (
              <StatsGraph key={effort} effort={effort} points={points} />
            ))}
          </section>

          <section className="bench-podiums-section">
            <h2>Podiums</h2>
            <p className="sub">Nombre de jeux où chaque moteur atteint le seuil</p>
            {BENCH_EFFORTS.map((effort) => (
              <PodiumSection
                key={effort}
                effort={effort}
                datasets={versions.datasets}
                engineRefs={versions.engine_refs}
              />
            ))}
          </section>
        </>
      )}
    </main>
  );
}
