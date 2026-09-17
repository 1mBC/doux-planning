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

const HOVER_THRESHOLD = 30;

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
        <section className="bench-stats-graphs">
          {graphs.map(({ effort, points }) => (
            <StatsGraph key={effort} effort={effort} points={points} />
          ))}
        </section>
      )}
    </main>
  );
}
