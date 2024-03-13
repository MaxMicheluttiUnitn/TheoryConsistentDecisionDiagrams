# Theory Consistent Decision Diagrams

Repository for the theorydd package

## Dumping T-BDDs and Abstraction-BDDs on dot files

The dd library was slightly changed to allow for .dot dumping as follows:

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
```
