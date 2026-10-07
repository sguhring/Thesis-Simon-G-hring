import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(8, 3.6), dpi=300)
fig.patch.set_alpha(0)
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

lines = [
    (r"$r_t = \mu + \varepsilon_t,\qquad \varepsilon_t = \sigma_t z_t,\qquad z_t \sim \mathcal{N}(0,1)$", 0.82, 20),
    (r"$\sigma_t^2 = \omega + \alpha\,\varepsilon_{t-1}^2 + \beta\,\sigma_{t-1}^2$", 0.55, 26),
    (r"$\omega > 0,\quad \alpha \geq 0,\quad \beta \geq 0,\quad \alpha + \beta < 1$", 0.30, 18),
    (r"$\bar{\sigma}^2 = \dfrac{\omega}{1 - \alpha - \beta}$", 0.09, 20),
]
for txt, y, size in lines:
    ax.text(0.5, y, txt, ha="center", va="center", fontsize=size, color="#0E1E3A")

fig.savefig("garch_formula.png", dpi=300, transparent=True)
print("ok")
