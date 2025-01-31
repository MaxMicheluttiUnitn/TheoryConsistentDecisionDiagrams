# Theory Consistent Decision Diagrams

Repository for the Python 3.10 theorydd package, which allows the generation and handling of Theory Consistent Decision Diagrams.

## Installing

First, install the dd dependency as follows:

```
    pip install --upgrade wheel cython
    export DD_FETCH=1 DD_CUDD=1
    pip install dd=0.5.7 -vvv --use-pep517 --no-build-isolation
```

You can check that the dependency is installed correctly if the following command does not give you ant errors:

```
    python -c 'import dd.cudd'
```

Now install the theorydd package (this package) from git

```
    pip install theorydd@git+https://github.com/MaxMicheluttiUnitn/TheoryConsistentDecisionDiagrams@main
```

After the pacckage and all the depnedencies have benn installed, use the pysmt-install tool to install the MathSAT SMT-solver. if you are using this package in a virtual environment, install the solver in a subfolder of the virtual environment folder by adding the option --install-path YOUR_VENV_FOLDER/solvers

```
    pysmt-install --msat
```

To check that everything is installed correctly type:

```
    python -c "from theorydd.theory_bdd import TheoryBDD as TBDD; import theorydd.formula as f; TBDD(f.default_phi())"
```

If you only see a imp warning, but no error message is displayed, everything should be installed correctly.

## Running Tabular AllSMT and the dDNNF compilers

This package supports both AllSMT solving through the Tabular AllSMT compiler and dDNNF compiling with c2d and d4.<br>
These components are not automatically installed with this package when pip is invoked.<br>
Instead a new command "theorydd_install" is installed on your machine which runs theorydd.install_bin.run_setup.<br>
To install all the components mentioned in this paragraph on your machine, run:

```
    theorydd_install --c2d --d4 --tabular
```

The options in the provided example are not required: you can install each component separately through the options of theorydd_install.

### Installing Manually

If you already own the binary for one of the compilers, you can copy
in the correct folder with the correct name as in the example below:

```
-theorydd
 |-abstractdd
 | L...
 |-bin
 | |-c2d
 | | L-c2d_linux
 | |-d4
 | | L-d4.bin
 | |-tabular
 | L L-tabularAllSMT.bin
 |-solvers
 | L...
 L ...
```

<!-- ## Dumping T-BDDs and Abstraction-BDDs on dot files

The dump BDDs on .dot files change the dd library code as follows:

```
def dump(self, filename, roots=None,
             filetype=None, **kw):
        if filetype is None:
            name = filename.lower()
            if name.endswith('.pdf'):
                filetype = 'pdf'
            elif name.endswith('.png'):
                filetype = 'png'
            elif name.endswith('.svg'):
                filetype = 'svg'
            elif name.endswith('.p'):
                filetype = 'pickle'
            elif name.endswith('.dot'):
                filetype = 'dot'
            else:
                raise Exception((
                    'cannot infer file type '
                    'from extension of file '
                    'name "{f}"').format(
                        f=filename))
        if filetype in ('pdf', 'png', 'svg', 'dot'):
            self._dump_figure(roots, filename,
                              filetype, **kw)
        elif filetype == 'pickle':
            self._dump_bdd(roots, filename, **kw)
        else:
            raise Exception(
                'unknown file type "{t}"'.format(
                    t=filetype))

    def _dump_figure(self, roots, filename,
                     filetype, **kw):
        """Write BDDs to `filename` as figure."""
        g = to_pydot(roots, self)
        if filetype == 'pdf':
            g.write_pdf(filename, **kw)
        elif filetype == 'png':
            g.write_png(filename, **kw)
        elif filetype == 'svg':
            g.write_svg(filename, **kw)
        elif filetype == 'dot':
            g.write(filename, **kw)
        else:
            raise Exception(
                'Unknown file type of "{f}"'.format(
                    f=filename))
``` -->

## Documentation

Documentation for this package is available [here](/docs/doc.md).

License
-------

theorydd is licensed under [MIT](LICENSE).