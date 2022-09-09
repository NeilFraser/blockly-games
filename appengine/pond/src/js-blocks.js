/**
 * @license
 * Copyright 2016 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * @fileoverview Redefining some of Blockly's exiting blocks to look more
 * similar to JavaScript.
 * @author fraser@google.com (Neil Fraser)
 * @author kozbial@google.com (Monica Kozbial)
 */
'use strict';

goog.provide('BlocklyGames.JsBlocks');

goog.require('Blockly');
goog.require('Blockly.Constants.Logic');
goog.require('Blockly.Constants.Loops');
goog.require('Blockly.Constants.Math');
goog.require('Blockly.Blocks.procedures');
goog.require('Blockly.Constants.Variables');
goog.require('Blockly.JavaScript');
goog.require('Blockly.JavaScript.logic');
goog.require('Blockly.JavaScript.loops');
goog.require('Blockly.JavaScript.math');
goog.require('Blockly.JavaScript.procedures');
goog.require('Blockly.JavaScript.variables');
goog.require('Blockly.Msg');
goog.require('BlocklyGames');


// Extensions to Blockly's existing blocks and JavaScript generator.

(function () {
  // Enclose mixin in an immediately executed function to hide the 'prop' var.
  for (const prop in Blockly.Constants.Logic.CONTROLS_IF_MUTATOR_MIXIN) {
    Blockly.Blocks['controls_if'][prop] =
        Blockly.Constants.Logic.CONTROLS_IF_MUTATOR_MIXIN[prop];
  }
})();

/**
 * If/elseif/else condition.
 * @this {Blockly.Block}
 */
Blockly.Blocks['controls_if'].init = function() {
  this.setHelpUrl(Blockly.Msg['CONTROLS_IF_HELPURL']);
  this.setColour(Blockly.Msg['LOGIC_HUE']);
  this.appendValueInput('IF0')
      .setCheck('Boolean')
      .appendField('if (');
  this.appendDummyInput()
      .appendField(') {');
  this.appendStatementInput('DO0');
  this.appendDummyInput('TAIL')
      .appendField('}');
  this.setInputsInline(true);
  this.setPreviousStatement(true);
  this.setNextStatement(true);
  this.setMutator(new Blockly.Mutator(['controls_if_elseif',
    'controls_if_else']));
  Blockly.Constants.Logic.CONTROLS_IF_TOOLTIP_EXTENSION.apply(this);
};

/**
 * Modify this block to have the correct number of inputs.
 * @private
 * @this {Blockly.Block}
 */
Blockly.Blocks['controls_if'].updateShape_ = function() {
  // Delete everything.
  if (this.getInput('ELSE')) {
    this.removeInput('ELSEMSG');
    this.removeInput('ELSE');
  }
  let i = 1;
  while (this.getInput('IF' + i)) {
    this.removeInput('IF' + i);
    this.removeInput('TAIL' + i);
    this.removeInput('DO' + i);
    i++;
  }
  // Rebuild block.
  for (let i = 1; i <= this.elseifCount_; i++) {
    this.appendValueInput('IF' + i)
        .setCheck('Boolean')
        .appendField('} else if (');
    this.appendDummyInput('TAIL' + i)
        .appendField(') {');
    this.appendStatementInput('DO' + i);
  }
  if (this.elseCount_) {
    this.appendDummyInput('ELSEMSG')
        .appendField('} else {');
    this.appendStatementInput('ELSE');
  }
  // Move final '}' to the end.
  this.moveInputBefore('TAIL', null);
};

/**
 * Comparison operator.
 * @this {Blockly.Block}
 */
Blockly.Blocks['logic_compare'].init = function() {
  const OPERATORS = [
    ['==', 'EQ'],
    ['!=', 'NEQ'],
    ['<', 'LT'],
    ['<=', 'LTE'],
    ['>', 'GT'],
    ['>=', 'GTE'],
  ];
  this.setHelpUrl(Blockly.Msg['LOGIC_COMPARE_HELPURL']);
  this.setColour(Blockly.Msg['LOGIC_HUE']);
  this.setOutput(true, 'Boolean');
  this.appendValueInput('A');
  this.appendValueInput('B')
      .appendField(new Blockly.FieldDropdown(OPERATORS), 'OP');
  this.setInputsInline(true);
  this.setTooltip(() => {
    const op = this.getFieldValue('OP');
    const TOOLTIPS = {
      'EQ': Blockly.Msg['LOGIC_COMPARE_TOOLTIP_EQ'],
      'NEQ': Blockly.Msg['LOGIC_COMPARE_TOOLTIP_NEQ'],
      'LT': Blockly.Msg['LOGIC_COMPARE_TOOLTIP_LT'],
      'LTE': Blockly.Msg['LOGIC_COMPARE_TOOLTIP_LTE'],
      'GT': Blockly.Msg['LOGIC_COMPARE_TOOLTIP_GT'],
      'GTE': Blockly.Msg['LOGIC_COMPARE_TOOLTIP_GTE'],
    };
    return TOOLTIPS[op];
  });
  this.prevBlocks_ = [null, null];
};

Blockly.Blocks['logic_boolean'].init = function() {
  this.jsonInit({
    "message0": "%1",
    "args0": [
      {
        "type": "field_dropdown",
        "name": "BOOL",
        "options": [
          ["true", "TRUE"],
          ["false", "FALSE"],
        ]
      }
    ],
    "output": "Boolean",
    "style": "logic_blocks",
    "tooltip": "%{BKY_LOGIC_BOOLEAN_TOOLTIP}",
    "helpUrl": "%{BKY_LOGIC_BOOLEAN_HELPURL}",
  });
};

Blockly.Blocks['logic_operation'].init = function() {
  this.jsonInit({
    "message0": "%1 %2 %3",
    "args0": [
      {
        "type": "input_value",
        "name": "A",
        "check": "Boolean",
      },
      {
        "type": "field_dropdown",
        "name": "OP",
        "options": [
          ["&&", "AND"],
          ["||", "OR"],
        ]
      },
      {
        "type": "input_value",
        "name": "B",
        "check": "Boolean"
      }
    ],
    "inputsInline": true,
    "output": "Boolean",
    "style": "logic_blocks",
    "helpUrl": "%{BKY_LOGIC_OPERATION_HELPURL}",
    "extensions": ["logic_op_tooltip"],
  });
};

/**
 * Block for 'while' loop.
 * @this {Blockly.Block}
 */
Blockly.Blocks['controls_whileUntil'].init = function() {
  this.jsonInit({
    "message0": "while ( %1 ) { %2 %3 }",
    "args0": [
      {
        "type": "input_value",
        "name": "BOOL",
        "check": "Boolean"
      },
      {
        "type": "input_dummy"
      },
      {
        "type": "input_statement",
        "name": "DO"
      }
    ],
    "inputsInline": true,
    "previousStatement": null,
    "nextStatement": null,
    "colour": Blockly.Msg['LOOPS_HUE'],
    "tooltip": Blockly.Msg['CONTROLS_WHILEUNTIL_TOOLTIP_WHILE'],
    "helpUrl": Blockly.Msg['CONTROLS_WHILEUNTIL_HELPURL'],
  });
};

/**
 * Block for basic arithmetic operator.
 * @this {Blockly.Block}
 */
Blockly.Blocks['math_arithmetic'].init = function() {
  this.jsonInit({
    "message0": "%1 %2 %3",
    "args0": [
      {
        "type": "input_value",
        "name": "A",
        "check": "Number"
      },
      {
        "type": "field_dropdown",
        "name": "OP",
        "options": [
          ["+", "ADD"],
          ["-", "MINUS"],
          ["*", "MULTIPLY"],
          ["/", "DIVIDE"]
        ]
      },
      {
        "type": "input_value",
        "name": "B",
        "check": "Number"
      }
    ],
    "inputsInline": true,
    "output": "Number",
    "colour": Blockly.Msg['MATH_HUE'],
    "helpUrl": Blockly.Msg['MATH_ARITHMETIC_HELPURL']
  });
  this.setTooltip(() => {
    const mode = this.getFieldValue('OP');
    const TOOLTIPS = {
      'ADD': Blockly.Msg['MATH_ARITHMETIC_TOOLTIP_ADD'],
      'MINUS': Blockly.Msg['MATH_ARITHMETIC_TOOLTIP_MINUS'],
      'MULTIPLY': Blockly.Msg['MATH_ARITHMETIC_TOOLTIP_MULTIPLY'],
      'DIVIDE': Blockly.Msg['MATH_ARITHMETIC_TOOLTIP_DIVIDE'],
    };
    return TOOLTIPS[mode];
  });
};

/**
 * Add to a variable in place.
 * @this {Blockly.Block}
 */
Blockly.Blocks['math_change'].init = function() {
  this.jsonInit({
    "message0": "%1 += %2;",
    "args0": [
      {
        "type": "field_variable",
        "name": "VAR",
        "variable": "name"
      },
      {
        "type": "input_value",
        "name": "DELTA",
        "check": "Number"
      }
    ],
    "inputsInline": true,
    "previousStatement": null,
    "nextStatement": null,
    "colour": Blockly.Msg['VARIABLES_HUE'],
    "helpUrl": Blockly.Msg['MATH_CHANGE_HELPURL']
  });
  this.setTooltip(() => {
    return Blockly.Msg['MATH_CHANGE_TOOLTIP'].replace('%1',
        this.getField('VAR').getVariable().name);
  });
};

/**
 * Defines the JavaScript generation for the change block, without checks as to
 * whether the variable is a number because users of games that use JsBlocks
 * are advanced and this reduces complexity in generated code.
 * @param {Blockly.Block} block
 * @returns {string}
 */
Blockly.JavaScript['math_change'] = function(block) {
  // Add to a variable in place.
  const delta = Blockly.JavaScript.valueToCode(block, 'DELTA',
      Blockly.JavaScript.ORDER_ADDITION) || '0';
  const varName = Blockly.JavaScript.nameDB_.getName(
      block.getFieldValue('VAR'), Blockly.Variables.NAME_TYPE);
  return varName + ' += ' + delta + ';\n';
};

Blockly.Blocks['math_random_float'].init = function() {
  this.jsonInit({
    "message0": "Math.random  (  )",
    "output": "Number",
    "style": "math_blocks",
    "tooltip": "%{BKY_MATH_RANDOM_FLOAT_TOOLTIP}",
    "helpUrl": "%{BKY_MATH_RANDOM_FLOAT_HELPURL}",
  });
};

/**
 * Variable getter.
 * @this {Blockly.Block}
 */
Blockly.Blocks['variables_get'].init = function() {
  this.setHelpUrl(Blockly.Msg['VARIABLES_GET_HELPURL']);
  this.setColour(Blockly.Msg['VARIABLES_HUE']);
  this.appendDummyInput()
      .appendField(new Blockly.FieldVariable('name'), 'VAR');
  this.setOutput(true);
  this.setTooltip(Blockly.Msg['VARIABLES_GET_TOOLTIP']);
  this.contextMenuMsg_ = Blockly.Msg['VARIABLES_GET_CREATE_SET'];
  this.contextMenuType_ = 'variables_set';
};

/**
 * Variable setter.
 * @this {Blockly.Block}
 */
Blockly.Blocks['variables_set'].init = function() {
  this.setHelpUrl(Blockly.Msg['VARIABLES_SET_HELPURL']);
  this.setColour(Blockly.Msg['VARIABLES_HUE']);
  this.appendValueInput('VALUE')
      .appendField('var')
      .appendField(new Blockly.FieldVariable('name'), 'VAR')
      .appendField('=');
  this.appendDummyInput()
      .appendField(';');
  this.setInputsInline(true);
  this.setPreviousStatement(true);
  this.setNextStatement(true);
  this.setTooltip(Blockly.Msg['VARIABLES_SET_TOOLTIP']);
  this.contextMenuMsg_ = Blockly.Msg['VARIABLES_SET_CREATE_GET'];
  this.contextMenuType_ = 'variables_get';
};

/**
 * Define a procedure with no return value.
 * @this {Blockly.Block}
 */
Blockly.Blocks['procedures_defnoreturn'].init = function() {
  const nameField = new Blockly.FieldTextInput('',
      Blockly.Procedures.rename);
  this.appendDummyInput()
      .appendField('function')
      .appendField(nameField, 'NAME')
      .appendField('(')
      .appendField('', 'PARAMS')
      .appendField(') {');
  // Append statement block to the function definition here.
  this.setStatements_(true);
  this.appendDummyInput()
      .appendField('}');
  this.setMutator(new Blockly.Mutator(['procedures_mutatorarg']));
  if (Blockly.Msg['PROCEDURES_DEFNORETURN_COMMENT']) {
    this.setCommentText(Blockly.Msg['PROCEDURES_DEFNORETURN_COMMENT']);
  }
  this.setColour(Blockly.Msg['PROCEDURES_HUE']);
  this.setTooltip(Blockly.Msg['PROCEDURES_DEFNORETURN_TOOLTIP']);
  this.setHelpUrl(Blockly.Msg['PROCEDURES_DEFNORETURN_HELPURL']);
  this.arguments_ = [];
  this.argumentVarModels_ = [];
  this.setStatements_(true);
  this.statementConnection_ = null;
};

/**
 * Define a procedure with a return value.
 * @this {Blockly.Block}
 */
Blockly.Blocks['procedures_defreturn'].init = function() {
  const nameField = new Blockly.FieldTextInput('',
      Blockly.Procedures.rename);
  this.appendDummyInput()
      .appendField('function')
      .appendField(nameField, 'NAME')
      .appendField('(')
      .appendField('', 'PARAMS')
      .appendField(') {');
  this.appendValueInput('RETURN')
      .setAlign(Blockly.ALIGN_RIGHT)
      .appendField('return');
  this.appendDummyInput()
      .appendField('}');
  this.setMutator(new Blockly.Mutator(['procedures_mutatorarg']));
  if (Blockly.Msg['PROCEDURES_DEFRETURN_COMMENT']) {
    this.setCommentText(Blockly.Msg['PROCEDURES_DEFRETURN_COMMENT']);
  }
  this.setColour(Blockly.Msg['PROCEDURES_HUE']);
  this.setTooltip(Blockly.Msg['PROCEDURES_DEFRETURN_TOOLTIP']);
  this.setHelpUrl(Blockly.Msg['PROCEDURES_DEFRETURN_HELPURL']);
  this.arguments_ = [];
  this.argumentVarModels_ = [];
  this.setStatements_(true);
  this.statementConnection_ = null;
};

Blockly.Msg['PROCEDURES_BEFORE_PARAMS'] = '';

/**
 * Call a procedure with no return value.
 * @this {Blockly.Block}
 */
Blockly.Blocks['procedures_callnoreturn'].init = function() {
  this.setHelpUrl(Blockly.Msg['PROCEDURES_CALLNORETURN_HELPURL']);
  this.setColour(Blockly.Msg['PROCEDURES_HUE']);
  this.appendDummyInput()
      .appendField('', 'NAME')
      .appendField('(');
  this.appendDummyInput('TAIL')
      .appendField(');');
  this.setInputsInline(true);
  this.setPreviousStatement(true);
  this.setNextStatement(true);
  this.setTooltip(Blockly.Msg['PROCEDURES_CALLNORETURN_TOOLTIP']);
  this.arguments_ = [];
  this.quarkConnections_ = {};
  this.quarkArguments_ = null;
};

/**
 * Modify this block to have the correct number of arguments.
 * @private
 * @this {Blockly.Block}
 */
Blockly.Blocks['procedures_callnoreturn'].updateShape_ = function() {
  let i;
  for (i = 0; i < this.arguments_.length; i++) {
    if (!this.getInput('ARG' + i)) {
      // Add new input.
      const field = new Blockly.FieldLabel(this.arguments_[i]);
      const input = this.appendValueInput('ARG' + i);
      if (i > 0) {
        input.appendField(',');
      }
      input.init();
    }
  }
  // Remove deleted inputs.
  while (this.getInput('ARG' + i)) {
    this.removeInput('ARG' + i);
    i++;
  }
  this.moveInputBefore('TAIL', null);
};

/**
 * Call a procedure with a return value.
 * @this {Blockly.Block}
 */
Blockly.Blocks['procedures_callreturn'].init = function() {
  this.setHelpUrl(Blockly.Msg['PROCEDURES_CALLRETURN_HELPURL']);
  this.setColour(Blockly.Msg['PROCEDURES_HUE']);
  this.appendDummyInput()
      .appendField('', 'NAME')
      .appendField('(');
  this.appendDummyInput('TAIL')
      .appendField(')');
  this.setInputsInline(true);
  this.setOutput(true);
  this.setTooltip(Blockly.Msg['PROCEDURES_CALLRETURN_TOOLTIP']);
  this.arguments_ = [];
  this.quarkConnections_ = {};
  this.quarkArguments_ = null;
};

Blockly.Blocks['procedures_callreturn'].updateShape_ =
    Blockly.Blocks['procedures_callnoreturn'].updateShape_;

// Don't show the "if/return" block.
delete Blockly.Blocks['procedures_ifreturn'];