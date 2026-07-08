import { addDefault, addNamed, addNamespace } from '@babel/helper-module-imports';
const _path = require('path')
const fs = require('fs');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;

function winPath(path) {
  return path.replace(/\\/g, '/');
}
export default class Plugin {
  constructor(libraryName, types, lintCheck, index = 0) {
    this.libraryName = libraryName;
    this.libraryDirectoryName = libraryName.split('/')[0];
    this.commonLibraryName = `${this.libraryDirectoryName}/iclient-common`
    this.types = types;
    this.lintCheck = lintCheck
    this.pluginStateKey = `importPluginState${index}`;
    this.resolvePath = '';
    this.mainFile = 'index.js'
    if(!this.lintCheck) {
      this.resolvePath = './node_modules'; 
    }
    this.libraryExportFiles = this.parseModules(`${this.libraryName}`);
  }
  getResolvePath(path) {
    return _path.resolve(this.resolvePath, path);
  }
  transformPath(path) {
    if(!path) {
      return path;
    }
    const index = path.indexOf(`/${this.libraryDirectoryName}/`);
    return path.substr(index + 1);
  }
  getLibraryDirectory(methodName) {
    const res = this.libraryExportFiles.find(item => {
      return item.exportName === methodName
    });
    const {file, exportDefault, exportExportedName, importAllAsName} = res || {};
    const path = this.transformPath(file)
    return { path, methodName: exportExportedName, transformToDefaultImport: exportDefault, importAllAsName }
  }
  isFile(path) {
    try {
      const stats = fs.statSync(this.getResolvePath(winPath(path)));
      return stats.isFile()
    }catch(e){
      return false;
    }
  }
  getExportEntiry(ast, dirnames, fileName, isExportName, isAddDefault) {
    const result = [];
    traverse(ast, {
      ExportNamedDeclaration: ({node}) => {
          // export function C(){} || class C(){}  node.declaration.type = FunctionDeclaration|ClassDeclaration
          if(node.declaration && node.declaration.id) {
            const exportExportedName = node.declaration.id.name;
            const entity = { exportExportedName, exportLocalName: exportExportedName, file: fileName, hasSource: false }
            if (isExportName) {
              entity.exportName = exportExportedName;
            }
            result.push(entity)
          }
          //  export const a = 1;
          if(node.declaration && node.declaration.declarations) {
            node.declaration.declarations.forEach(declaration=>{
              const exportExportedName = declaration.id.name;
              const entity = { exportExportedName, exportLocalName: exportExportedName, file: fileName, hasSource: false }
              if (isExportName) {
                entity.exportName = exportExportedName;
              }
              result.push(entity)
            })
          }
          // export {xxx}  export {local as exported}  export * as xxx from './xxx'
          node.specifiers.forEach(specifier=>{
            const exportExportedName = specifier.exported.name;
            let entity = { exportExportedName, exportLocalName: specifier.local && specifier.local.name || exportExportedName, file: fileName, hasSource: false }
            if(node.source) {
              const sourceValue = node.source.value
              const file = this.getDirFilePath(sourceValue, dirnames);
              entity = { ...entity, file, hasSource: true }
              //  export * as xxx from './xxx'
              if(!specifier.local) {
                entity.hasSource = false;
                entity.importAllAsName = true;
              }
            }
            if (isExportName) {
              entity.exportName = exportExportedName;
            }
            if(entity.exportName === 'default') {
              entity.exportDefault= true;
              entity.isExportName = isExportName;
            }
            result.push(entity)
          })
      },
      ExportAllDeclaration: ({node}) => {
        // export * from 'xxx';
        result.push({ hasExportAll: true, file: this.getDirFilePath(node.source.value, dirnames), hasSource: true })
      },
      ExportDefaultDeclaration: ({node}) => {
        if(isAddDefault) {
          result.push({ exportDefault: true, file: fileName, isAddDefault });
        }
      },
    })
    return result;
  }
  getEntityInexsByLocalName(exportEntity=[], localName) {
    // import {A} from 'xxx' export {A, A as B}
    const res = [];
    exportEntity && exportEntity.forEach((item, index) => {
      if(item.exportLocalName === localName){
        res.push(index)
      }
    });
    return res;
  }
  getSource(ast, exportEntity=[], dirnames) {
    traverse(ast, {
      ImportDeclaration: ({node}) => {
        node.specifiers.forEach(specifier=>{
          const sourceValue = node.source.value
          const file = this.getDirFilePath(sourceValue, dirnames);
          const importLocalName = specifier.local.name;
          const entityIndexs = this.getEntityInexsByLocalName(exportEntity, importLocalName);
          if (entityIndexs.length > 0) {
            entityIndexs.forEach((entityIndex)=>{
              const entity = exportEntity[entityIndex];
              exportEntity[entityIndex] = { ...entity, file, hasSource: true, importDefault: false, importLocalName: importLocalName, importImportedName: specifier.imported && specifier.imported.name };
            })
            if (specifier.type ==='ImportSpecifier') {
              // import {xxx} from "xxx"  import {xxx as xxx} from "xxx"(imported as local)
            }
            if (specifier.type === 'ImportDefaultSpecifier') {
              // import xxx from "xxx"
              entityIndexs.forEach((entityIndex)=>{
                exportEntity[entityIndex].importDefault = true;
              });
            }
            if (specifier.type ==='ImportNamespaceSpecifier') {
              // import * as xxx from "xxx"
              entityIndexs.forEach((entityIndex)=>{
                exportEntity[entityIndex].hasSource = false;
                exportEntity[entityIndex].importAllAsName = true;
              });
            }
          }
      })
      }
    })
    return exportEntity;
  }
  checkFilePath(abspath) {
    if(this.isFile(abspath)) {
      return winPath(abspath)
    }
  }
  getDirFilePath(sourceValue, dirnames) {
    if (sourceValue.includes(this.commonLibraryName)) {
      if (this.lintCheck) {
        sourceValue = sourceValue.replace(this.commonLibraryName, './src/common');
        const abspath =  _path.join(process.cwd(), sourceValue + '.js')
        const abspath1 =  _path.join(process.pwd(), sourceValue + 'index.js')
        return this.checkFilePath(abspath) || this.checkFilePath(abspath1)
      } else {
        sourceValue = "../../".concat(sourceValue);
      }        
    }
    const abspath = _path.join(dirnames, sourceValue + '.js');
    const abspath1 = _path.join(dirnames, sourceValue ,'index.js');
    const abspath2 = _path.join(dirnames, sourceValue);
    return this.checkFilePath(abspath) || this.checkFilePath(abspath1) || this.checkFilePath(abspath2);
  }
  getModuleInfo(file, isExportName = false, isAddDefault = true){
    if(!file) {
      return [];
    }
    // 加node_modules;
    const resolvePath = this.getResolvePath(file);
    const dirnames = winPath(_path.dirname(resolvePath));
    const fileContent = fs.readFileSync(resolvePath,'utf-8').toString();
    const ast = parser.parse(fileContent, {sourceType: 'module'});
    const exportEntity = this.getExportEntiry(ast, dirnames, file, isExportName, isAddDefault);
    this.getSource(ast, exportEntity, dirnames);
    return [...exportEntity];
  }
  parseModules(libraryName, mainFile = this.mainFile){
    const entryFile = `${libraryName}/${mainFile}`
    let exportEntity = this.getModuleInfo(entryFile, true)
    // 拿到所有导出的
    for (let index = 0; index < exportEntity.length; index++) {
      const entity = exportEntity[index];
      const { file, hasSource, hasExportAll } = entity;
      if (hasExportAll && hasSource) {
        exportEntity.splice(index, 1);
        exportEntity.push(...this.getModuleInfo(file, true, index === 0))
        index = index - 1;
      }
    }
    for (let i = 0; i < exportEntity.length; i++) {
      const entity = exportEntity[i];
      const { hasSource, file, exportName, importDefault, importImportedName, exportLocalName } = entity;
      if(hasSource) {
        const sourceEntity = this.getModuleInfo(file);
        const newEntity = sourceEntity.find(item => { return (importDefault && item.exportDefault) || ((importImportedName || exportLocalName) === item.exportExportedName)})
        if (!newEntity) {
          throw new Error(`${exportName} not found in "${file}"`);
        } else {
          if(!newEntity.hasSource) {
            newEntity.hasSource = false;
          }
          exportEntity[i] = {...entity, ...newEntity, exportName};
          i = i - 1;
        }
      }
    }
    return exportEntity;
  }

  getPluginState(state) {
    if (!state[this.pluginStateKey]) {
      state[this.pluginStateKey] = {}; // eslint-disable-line
    }
    return state[this.pluginStateKey];
  }

  importMethod(methodName, file, pluginState) {
    if (!pluginState.selectedMethods[methodName]) {
      const { path: libraryDirectory, methodName: transformedMethodName, transformToDefaultImport, importAllAsName} = this.getLibraryDirectory(methodName);
      if(!libraryDirectory) {
        throw new Error(`${methodName} not found in "${this.libraryName}"`);
      }
      const path2 = winPath(_path.join.call(void 0, libraryDirectory));
      if (importAllAsName) {
        pluginState.selectedMethods[methodName] = addNamespace.call(void 0, file.path, path2, {nameHint: transformedMethodName})
      } else if(transformToDefaultImport) {
        pluginState.selectedMethods[methodName] = addDefault.call(void 0, file.path, path2, {nameHint: transformedMethodName})
      } else {
        pluginState.selectedMethods[methodName] = addNamed.call(void 0, file.path, transformedMethodName, path2);
      }
    }
    return {...pluginState.selectedMethods[methodName]};
  }

  buildExpressionHandler(node, props, path, state) {
    const file = (path && path.hub && path.hub.file) || (state && state.file);
    const { types } = this;
    const pluginState = this.getPluginState(state);
    props.forEach(prop => {
      if (!types.isIdentifier(node[prop])) return;
      if (
        pluginState.specified[node[prop].name] &&
        types.isImportSpecifier(path.scope.getBinding(node[prop].name).path)
      ) {
        node[prop] = this.importMethod(pluginState.specified[node[prop].name], file, pluginState); // eslint-disable-line
      }
    });
  }

  buildDeclaratorHandler(node, prop, path, state) {
    const file = (path && path.hub && path.hub.file) || (state && state.file);
    const { types } = this;
    const pluginState = this.getPluginState(state);

    const checkScope = targetNode =>
      pluginState.specified[targetNode.name] && // eslint-disable-line
      path.scope.hasBinding(targetNode.name) && // eslint-disable-line
      path.scope.getBinding(targetNode.name).path.type === 'ImportSpecifier'; // eslint-disable-line

    if (types.isIdentifier(node[prop]) && checkScope(node[prop])) {
      node[prop] = this.importMethod(pluginState.specified[node[prop].name], file, pluginState); // eslint-disable-line
    } else if (types.isSequenceExpression(node[prop])) {
      node[prop].expressions.forEach((expressionNode, index) => {
        if (types.isIdentifier(expressionNode) && checkScope(expressionNode)) {
          node[prop].expressions[index] = this.importMethod(
            pluginState.specified[expressionNode.name],
            file,
            pluginState,
          ); // eslint-disable-line
        }
      });
    }
  }

  ProgramEnter(path, state) {
    const pluginState = this.getPluginState(state);
    pluginState.specified = Object.create(null);
    pluginState.libraryObjs = Object.create(null);
    pluginState.selectedMethods = Object.create(null);
    pluginState.pathsToRemove = [];
  }

  ProgramExit(path, state) {
    this.getPluginState(state).pathsToRemove.forEach(p => !p.removed && p.remove());
  }

  ImportDeclaration(path, state) {
    const { node } = path;

    // path maybe removed by prev instances.
    if (!node) return;

    const { value } = node.source;
    const { libraryName } = this;
    const { types } = this;
    const pluginState = this.getPluginState(state);
    if (value === libraryName) {
      node.specifiers.forEach(spec => {
        if (types.isImportSpecifier(spec)) {
          pluginState.specified[spec.local.name] = spec.imported.name;
        } else {
          pluginState.libraryObjs[spec.local.name] = true;
        }
      });
      pluginState.pathsToRemove.push(path);
    }
  }

  CallExpression(path, state) {
    const { node } = path;
    const file = (path && path.hub && path.hub.file) || (state && state.file);
    const { name } = node.callee;
    const { types } = this;
    const pluginState = this.getPluginState(state);

    if (types.isIdentifier(node.callee)) {
      if (pluginState.specified[name]) {
        node.callee = this.importMethod(pluginState.specified[name], file, pluginState);
      }
    }

    node.arguments = node.arguments.map(arg => {
      const { name: argName } = arg;
      if (
        pluginState.specified[argName] &&
        path.scope.hasBinding(argName) &&
        path.scope.getBinding(argName).path.type === 'ImportSpecifier'
      ) {
        return this.importMethod(pluginState.specified[argName], file, pluginState);
      }
      return arg;
    });
  }

  MemberExpression(path, state) {
    const { node } = path;
    const file = (path && path.hub && path.hub.file) || (state && state.file);
    const pluginState = this.getPluginState(state);

    // multiple instance check.
    if (!node.object || !node.object.name) return;

    if (pluginState.libraryObjs[node.object.name]) {
      path.replaceWith(this.importMethod(node.property.name, file, pluginState));
    } else if (pluginState.specified[node.object.name] && path.scope.hasBinding(node.object.name)) {
      const { scope } = path.scope.getBinding(node.object.name);
      // global variable in file scope
      if (scope.path.parent.type === 'File') {
        node.object = this.importMethod(pluginState.specified[node.object.name], file, pluginState);
      }
    }
  }

  Property(path, state) {
    const { node } = path;
    this.buildDeclaratorHandler(node, 'value', path, state);
  }

  VariableDeclarator(path, state) {
    const { node } = path;
    this.buildDeclaratorHandler(node, 'init', path, state);
  }

  ArrayExpression(path, state) {
    const { node } = path;
    const props = node.elements.map((_, index) => index);
    this.buildExpressionHandler(node.elements, props, path, state);
  }

  LogicalExpression(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['left', 'right'], path, state);
  }

  ConditionalExpression(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['test', 'consequent', 'alternate'], path, state);
  }

  IfStatement(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['test'], path, state);
    this.buildExpressionHandler(node.test, ['left', 'right'], path, state);
  }

  ExpressionStatement(path, state) {
    const { node } = path;
    const { types } = this;
    if (types.isAssignmentExpression(node.expression)) {
      this.buildExpressionHandler(node.expression, ['right'], path, state);
    }
  }

  ReturnStatement(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['argument'], path, state);
  }

  ExportDefaultDeclaration(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['declaration'], path, state);
  }

  BinaryExpression(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['left', 'right'], path, state);
  }

  NewExpression(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['callee'], path, state);

    const argumentsProps = node.arguments.map((_, index) => index);
    this.buildExpressionHandler(node.arguments, argumentsProps, path, state);
  }

  SwitchStatement(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['discriminant'], path, state);
  }

  SwitchCase(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['test'], path, state);
  }

  ClassDeclaration(path, state) {
    const { node } = path;
    this.buildExpressionHandler(node, ['superClass'], path, state);
  }
}
