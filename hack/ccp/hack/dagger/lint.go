package main

func (m *CCP) Lint() *Container {
	return dag.GolangciLint(GolangciLintOpts{
		Version:   golangciLintVersion,
		GoVersion: goVersion,
	}).
		Run(m.Source, GolangciLintRunOpts{
			Verbose: true,
		})
}
